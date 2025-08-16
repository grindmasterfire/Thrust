"""
mute_cleaner.py
----------------

This module extends THRUST's memory management capabilities by
providing a higher‑level interface for cleaning up Python objects,
releasing unused resources and performing deep cache purges.  It
complements the ``ThrustCore.flush_memory`` method by distinguishing
between a lightweight "soft" clean and a more aggressive memory
scavenge.

In the **soft** mode, ``MuteCleaner`` will run the Python garbage
collector and attempt to close long‑idle file descriptors.  This is
useful when you want to reclaim RAM without impacting the operating
system's page cache or kernel structures.  In **aggressive** mode,
``MuteCleaner`` delegates to ``ThrustCore.flush_memory`` with
``aggressive=True`` which triggers platform‑specific mechanisms to
drop caches and minimise the working set【401947524794586†L100-L136】【537074957523770†L122-L149】.

Example usage::

    from src.mute_cleaner import MuteCleaner
    cleaner = MuteCleaner()
    cleaner.soft_clean()      # reclaim Python memory only
    cleaner.aggressive_clean()  # drop OS caches (may require privileges)

Note: The aggressive clean may require elevated privileges on some
platforms.  Errors are logged but not raised.
"""

from __future__ import annotations

import gc
import logging
import os
import psutil  # type: ignore
import time
from typing import Optional

# Import ThrustCore either relative to this package (when used as part of
# the ``src`` package) or from the top‑level module (when ``src`` is
# added to ``sys.path``).  The relative import may fail if the module
# is executed outside of a package context.
try:
    from .thrust_core import ThrustCore  # type: ignore
except Exception:
    # Fallback to absolute import when src is on sys.path
    from thrust_core import ThrustCore  # type: ignore

logger = logging.getLogger("thrust.mute")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class MuteCleaner:
    """Perform soft or aggressive memory cleaning operations."""

    def __init__(self, engine: Optional[ThrustCore] = None) -> None:
        # Accept an existing ThrustCore instance for aggressive flushes
        self.engine = engine or ThrustCore()

    def _close_idle_fds(self) -> int:
        """Attempt to close idle file descriptors using psutil.

        Returns the number of descriptors closed.  On Unix platforms
        ``psutil`` can enumerate open files for the current process.  We
        consider a descriptor idle if it hasn't been accessed in more
        than 60 seconds.  This is a heuristic; long‑held descriptors
        (e.g. sockets) are not touched.  On platforms where this
        information isn't available, the method returns zero.
        """
        closed = 0
        try:
            p = psutil.Process()
            now = time.time()
            for f in p.open_files():
                # ``f.pid`` is not present; ``p.open_files`` returns
                # named tuples with ``fd`` and ``path``.  We skip
                # descriptors with no fd or unknown stat.
                fd = f.fd
                if fd is None or fd < 0:
                    continue
                try:
                    stat = os.fstat(fd)
                    atime = stat.st_atime
                    # close if accessed more than 60s ago
                    if now - atime > 60:
                        os.close(fd)
                        closed += 1
                except Exception:
                    continue
        except Exception:
            # psutil may not be available or open_files may not be
            # implemented on some platforms (e.g. Windows).  We silently
            # ignore errors here.
            pass
        return closed

    def soft_clean(self) -> None:
        """Reclaim Python memory and close idle file descriptors.

        This method runs the garbage collector to free unused Python
        objects and attempts to close file descriptors that have not
        been accessed recently.  It does **not** drop OS caches or
        purge kernel structures, so it is safe to run frequently.
        """
        collected = gc.collect()
        closed = self._close_idle_fds()
        logger.info(f"Soft clean: collected {collected} objects, closed {closed} idle FDs")

    def aggressive_clean(self) -> None:
        """Perform an aggressive memory flush using ``ThrustCore``.

        Delegates to ``ThrustCore.flush_memory(aggressive=True)`` which
        triggers platform‑specific cache dropping mechanisms.  This
        operation may require elevated privileges.  Any exceptions are
        logged but not propagated to the caller.
        """
        try:
            # Always perform a soft clean first to free Python objects
            collected = gc.collect()
            logger.info(f"Aggressive clean: collected {collected} objects")
            self.engine.flush_memory(aggressive=True)
        except Exception as exc:
            logger.warning(f"Failed to perform aggressive clean: {exc}")