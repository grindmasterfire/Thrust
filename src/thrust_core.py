"""
thrust_core.py
----------------

This module implements the core functionality for **THRUST**, a lightweight
cross‑platform acceleration utility designed to improve the local performance
of AI models such as GPT4All, Claude CLI, Mistral, Ollama and LM Studio.  The
goal of THRUST is to provide runtime hooks that adjust CPU affinity,
process scheduling, memory usage and caching in order to reduce inference
latency – especially on resource constrained systems.

The implementation below uses the open‑source ``psutil`` library and
standard Python modules to interact with the underlying operating system.  On
platforms that support it (Linux, Windows and FreeBSD) ``psutil.Process()
.cpu_affinity()`` can get and set a process’s CPU affinity list【137749184164406†L1898-L1919】.  Adjusting
the CPU affinity can pin an AI container or CLI to a subset of cores which
helps reduce context switching and improves cache locality.  On POSIX
systems where ``psutil`` does not expose affinity (such as certain BSDs or
macOS) the module falls back to ``os.sched_setaffinity`` which provides
similar functionality【650715465564316†L80-L93】.

Process priority (sometimes called “niceness”) is another lever exposed
through ``psutil.Process.nice()``.  On UNIX systems the niceness value
typically ranges from ‑20 (highest priority) to 19 (lowest)【137749184164406†L1660-L1670】, while
on Windows the API maps to discrete priority classes (e.g. ``HIGH_PRIORITY_CLASS``)
【137749184164406†L1672-L1679】.  Increasing the priority of a model process can help ensure it
receives more CPU time when the system is under load.

Clearing memory caches can reduce fragmentation and free up RAM for model
parameters.  On Linux the kernel allows users with sufficient privileges to
drop page caches, dentries and inode caches by writing ``1``, ``2`` or ``3`` to
``/proc/sys/vm/drop_caches``【401947524794586†L100-L136】.  On Windows the
``EmptyWorkingSet`` function from the Process Status API removes as many
pages as possible from a process’s working set【537074957523770†L122-L149】.  THRUST
wraps these mechanisms behind a single ``flush_memory()`` call that first
runs the Python garbage collector and then performs more aggressive flushing
depending on the platform.

The module exposes a ``ThrustCore`` class that encapsulates state (e.g.
original affinity and priority values) and provides high‑level methods for
benchmarking commands, detecting running AI runtimes, applying boosts and
prefetching model files into cache.  A thin CLI wrapper lives in ``bin/thrust``.

``NOTE``: Some operations (such as decreasing the niceness below zero or
dropping kernel caches) may require elevated privileges.  THRUST will log
warnings if it lacks permission to perform an action.  All operations are
implemented with sensible fallbacks so they can run on Windows, Linux and
macOS without crashing.
"""

from __future__ import annotations

import gc
import json
import logging
import os
import platform
import subprocess
import sys
import time
from typing import Iterable, List, Optional

try:
    import psutil  # type: ignore
except ImportError as e:
    raise RuntimeError(
        "psutil is required for thrust_core but is not installed. Please install psutil >= 5.0"
    ) from e

try:
    import ctypes  # Only used on Windows for EmptyWorkingSet
except ImportError:
    ctypes = None  # type: ignore


#: Create a module‑level logger.  Consumers can override the handler/level as desired.
logger = logging.getLogger("thrust")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ThrustCore:
    """Core functionality for the THRUST accelerator.

    This class exposes methods to set and restore CPU affinity, change process
    priority, flush memory caches, prefetch model files, detect running AI
    runtimes and benchmark arbitrary commands.  It stores the original
    affinity and priority so that callers can later restore them via
    ``reset_cpu_affinity`` and ``reset_priority``.
    """

    def __init__(self, config: Optional[dict] | None = None) -> None:
        self.config: dict = config or {}
        # Remember original affinity and niceness to allow restoration
        self._original_affinity: Optional[Iterable[int]] = None
        self._original_nice: Optional[int | str] = None

    # ------------------------------------------------------------------
    # Configuration loading
    #
    def load_config(self, path: str) -> dict:
        """Load a JSON configuration file into the engine.

        The configuration file (often named ``.thrustrc``) can define
        parameters like default CPU cores, nice value or whether to run in
        aggressive flush mode.  Unknown keys are preserved so that future
        releases can add options without breaking compatibility.

        :param path: Path to a JSON‑formatted configuration file.
        :returns: The merged configuration dictionary.
        """
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("Configuration file must contain a JSON object")
            self.config.update(data)
            logger.info(f"Loaded configuration from {path}: {data}")
            return self.config
        except Exception as exc:
            logger.error(f"Failed to load config {path}: {exc}")
            raise

    # ------------------------------------------------------------------
    # CPU affinity management
    #
    def set_cpu_affinity(self, cpus: Optional[Iterable[int]]) -> Optional[Iterable[int]]:
        """Set the CPU affinity of the current process.

        When a list of CPU indices is provided, the engine will attempt to pin
        the Python process to those cores.  On Linux, Windows and FreeBSD this
        uses ``psutil.Process().cpu_affinity()``【137749184164406†L1898-L1919】.  If that method is not available
        (e.g. on some BSDs or macOS) it falls back to ``os.sched_setaffinity``
        which is only available on certain UNIX platforms【650715465564316†L80-L93】.

        If ``cpus`` is ``None`` then no action is taken and the existing
        affinity is returned.  The original affinity is stored on the first
        call so that it can later be restored.

        :param cpus: Iterable of CPU indices (e.g. [0, 1]). ``None`` means
          return without modifying affinity.
        :returns: The previous affinity list if a change was made, else ``None``.
        """
        if cpus is None:
            return None

        p = psutil.Process()
        # Save original affinity once
        if self._original_affinity is None:
            try:
                if hasattr(p, "cpu_affinity"):
                    self._original_affinity = p.cpu_affinity()
                elif hasattr(os, "sched_getaffinity"):
                    self._original_affinity = list(os.sched_getaffinity(0))
            except Exception:
                # If fetching affinity fails we still proceed; original stays None
                pass

        try:
            # Primary implementation using psutil
            if hasattr(p, "cpu_affinity"):
                p.cpu_affinity(list(cpus))
                logger.info(f"Set CPU affinity to {list(cpus)}")
                return self._original_affinity
            # Fallback for Linux/Unix where psutil lacks cpu_affinity
            if hasattr(os, "sched_setaffinity"):
                os.sched_setaffinity(0, set(cpus))  # type: ignore[arg-type]
                logger.info(f"Set CPU affinity via os.sched_setaffinity to {list(cpus)}")
                return self._original_affinity
        except Exception as exc:
            logger.warning(f"Failed to set CPU affinity: {exc}")
        return None

    def reset_cpu_affinity(self) -> None:
        """Restore the CPU affinity of the current process to its original state."""
        if self._original_affinity is None:
            return
        p = psutil.Process()
        try:
            if hasattr(p, "cpu_affinity"):
                p.cpu_affinity(list(self._original_affinity))  # type: ignore[arg-type]
                logger.info(f"Restored CPU affinity to {list(self._original_affinity)}")
            elif hasattr(os, "sched_setaffinity"):
                os.sched_setaffinity(0, set(self._original_affinity))  # type: ignore[arg-type]
                logger.info(f"Restored CPU affinity via os.sched_setaffinity to {list(self._original_affinity)}")
        except Exception as exc:
            logger.warning(f"Failed to restore CPU affinity: {exc}")
        finally:
            self._original_affinity = None

    # ------------------------------------------------------------------
    # Process priority management
    #
    def set_priority(self, nice_value: Optional[int | str] = None) -> Optional[int | str]:
        """Adjust the niceness or priority class of the current process.

        On UNIX, a lower nice value corresponds to a higher priority and the range
        typically spans from ‑20 (highest) to +19 (lowest)【137749184164406†L1660-L1670】.  On Windows, ``psutil``
        exposes constants like ``HIGH_PRIORITY_CLASS`` and ``REALTIME_PRIORITY_CLASS``
        which map to the Windows process priority classes【137749184164406†L1672-L1679】.

        If ``nice_value`` is ``None``, THRUST will select a sensible default
        (``HIGH_PRIORITY_CLASS`` on Windows or ``-5`` on POSIX).  The original
        niceness/priority is stored and returned for later restoration.

        :param nice_value: Either an integer niceness (POSIX) or a psutil
            priority constant (Windows).  If ``None`` a default is chosen.
        :returns: The previous niceness/priority class, or ``None`` on error.
        """
        p = psutil.Process()
        # Capture original priority only once
        try:
            if self._original_nice is None:
                self._original_nice = p.nice()
        except Exception:
            pass
        # Determine target
        target = nice_value
        if nice_value is None:
            if os.name == "nt":
                target = psutil.HIGH_PRIORITY_CLASS  # type: ignore[assignment]
            else:
                target = -5
        try:
            p.nice(target)  # type: ignore[arg-type]
            logger.info(f"Set process priority to {target}")
            return self._original_nice
        except Exception as exc:
            logger.warning(f"Failed to set process priority: {exc}")
            return None

    def reset_priority(self) -> None:
        """Restore the process priority to its original value."""
        if self._original_nice is None:
            return
        p = psutil.Process()
        try:
            p.nice(self._original_nice)  # type: ignore[arg-type]
            logger.info(f"Restored process priority to {self._original_nice}")
        except Exception as exc:
            logger.warning(f"Failed to restore process priority: {exc}")
        finally:
            self._original_nice = None

    # ------------------------------------------------------------------
    # Memory management
    #
    def flush_memory(self, aggressive: bool = False) -> None:
        """Flush Python and system memory caches.

        This method first invokes the garbage collector to reclaim Python objects.
        If ``aggressive`` is ``True``, it then performs an OS specific flush:

        * On Linux the kernel page cache, dentries and inode caches are dropped
          by writing ``3`` to ``/proc/sys/vm/drop_caches``【401947524794586†L100-L136】.
        * On Windows it calls the ``EmptyWorkingSet`` API which removes pages
          from the process's working set【537074957523770†L122-L149】.
        * On macOS it tries to run the ``purge`` command to free file system
          caches (works on some macOS versions).

        Many of these operations require elevated privileges.  Errors are
        logged but do not raise exceptions so that applications can continue
        running safely.

        :param aggressive: Whether to perform kernel/OS‑level cache clearing.
        """
        # Always run Python's garbage collector
        collected = gc.collect()
        logger.info(f"Garbage collector collected {collected} objects")

        if not aggressive:
            return
        logger.info("Performing aggressive memory flush")
        # POSIX: sync and drop caches
        if os.name == "posix":
            # flush pending writes to disk
            try:
                subprocess.call(["sync"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as exc:
                logger.warning(f"Failed to run sync: {exc}")
            # Linux: drop page/dentry/inode caches
            if sys.platform.startswith("linux"):
                try:
                    with open("/proc/sys/vm/drop_caches", "w", encoding="utf-8") as f:
                        # writing '3' frees pagecache, dentries and inodes【401947524794586†L100-L136】
                        f.write("3\n")
                    logger.info("Dropped Linux caches via /proc/sys/vm/drop_caches")
                except Exception as exc:
                    logger.warning(f"Failed to drop Linux caches: {exc}")
            # macOS: use purge command if available
            elif sys.platform == "darwin":
                try:
                    subprocess.call(["purge"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.info("Invoked macOS purge command")
                except Exception as exc:
                    logger.warning(f"Failed to run purge: {exc}")
        # Windows: call EmptyWorkingSet via ctypes
        elif os.name == "nt":
            if ctypes is not None:
                try:
                    hprocess = ctypes.windll.kernel32.GetCurrentProcess()
                    # remove pages from working set (as many as possible)【537074957523770†L122-L149】
                    ctypes.windll.psapi.EmptyWorkingSet(hprocess)
                    logger.info("Called EmptyWorkingSet to reduce working set size")
                except Exception as exc:
                    logger.warning(f"Failed to call EmptyWorkingSet: {exc}")
        else:
            logger.warning("Aggressive flush not supported on this platform")

    # ------------------------------------------------------------------
    # Model prefetching
    #
    def prefetch_model(self, path: str, chunk_size: int = 1024 * 1024) -> Optional[float]:
        """Read a model file into memory to warm up disk and OS caches.

        By reading the file in chunks we can cause the operating system to
        populate its page cache.  This can reduce latency during the first
        inference call if the model has not been loaded recently.  If the file
        does not exist or cannot be read then an error is logged and ``None`` is
        returned.

        :param path: Path to the model file on disk.
        :param chunk_size: Size of each read in bytes.
        :returns: Time in seconds spent reading the file, or ``None`` on error.
        """
        start = time.time()
        try:
            total_read = 0
            with open(path, "rb") as fh:
                while True:
                    buf = fh.read(chunk_size)
                    if not buf:
                        break
                    total_read += len(buf)
            elapsed = time.time() - start
            logger.info(f"Prefetched {total_read / (1024 * 1024):.2f} MB from {path} in {elapsed:.2f} seconds")
            return elapsed
        except Exception as exc:
            logger.error(f"Failed to prefetch model {path}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Runtime detection and boosting
    #
    def auto_detect_runtime(self) -> List[psutil.Process]:
        """Scan running processes for common local LLM runtimes.

        THRUST supports hooking into community models run via Ollama, LM Studio,
        GPT4All, Mistral or similar executables.  This method walks the process
        table and returns a list of matching ``psutil.Process`` objects whose
        ``name`` or command line contains one of a predefined set of keywords.
        Errors due to insufficient permissions are ignored.

        :returns: List of ``psutil.Process`` instances representing detected
          LLM runtimes.
        """
        keywords = [
            "ollama",
            "lm studio",
            "lmstudio",
            "gpt4all",
            "mistral",
            "claude",
            "mojo",
            "llama",
        ]
        matches: List[psutil.Process] = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                # Compose a lowercase string of process name and command line
                name = (proc.info.get("name") or "").lower()
                cmd = " ".join(proc.info.get("cmdline") or []).lower()
                if any(kw in name or kw in cmd for kw in keywords):
                    matches.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return matches

    def apply_boost(self, process: psutil.Process, cpus: Optional[Iterable[int]] = None, nice_value: Optional[int | str] = None) -> None:
        """Apply CPU affinity and priority boosts to another process.

        This helper is used when THRUST detects external runtimes and needs to
        adjust their scheduling parameters.  It accepts an existing
        ``psutil.Process`` object and optional CPU and nice values.

        :param process: A ``psutil.Process`` instance to modify.
        :param cpus: Iterable of CPU indices to assign as the new affinity.
        :param nice_value: Custom niceness/priority to apply.  See ``set_priority``.
        """
        # CPU affinity
        if cpus is not None and hasattr(process, "cpu_affinity"):
            try:
                process.cpu_affinity(list(cpus))
                logger.info(f"Set CPU affinity of PID {process.pid} to {list(cpus)}")
            except Exception as exc:
                logger.warning(f"Failed to set CPU affinity for PID {process.pid}: {exc}")
        # Priority
        try:
            if nice_value is not None:
                process.nice(nice_value)  # type: ignore[arg-type]
            else:
                if os.name == "nt":
                    process.nice(psutil.HIGH_PRIORITY_CLASS)  # type: ignore[arg-type]
                else:
                    process.nice(-5)
            logger.info(f"Adjusted priority for PID {process.pid}")
        except Exception as exc:
            logger.warning(f"Failed to adjust priority for PID {process.pid}: {exc}")

    # ------------------------------------------------------------------
    # Benchmarking
    #
    def benchmark_command(self, command: str, args: Optional[List[str]] = None, runs: int = 1) -> List[float]:
        """Measure the execution time of an external command.

        The command is run synchronously ``runs`` times using ``subprocess.run``.
        Durations are measured using ``time.time()``.  If the command fails
        (non‑zero exit code or exception) an empty list is returned and an
        error logged.

        :param command: Name or path of the executable to run.
        :param args: Additional arguments passed to the command.
        :param runs: Number of times to execute the command.
        :returns: A list of elapsed times (seconds) for each run.
        """
        durations: List[float] = []
        for i in range(max(1, runs)):
            start = time.time()
            try:
                # Run the command; combine command and args into a single list
                cmdline = [command] + (args or [])
                subprocess.run(cmdline, check=True)
                durations.append(time.time() - start)
            except Exception as exc:
                logger.error(f"Benchmark run failed: {exc}")
                return []
        return durations
