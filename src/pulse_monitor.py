"""
pulse_monitor.py
-----------------

This module implements a lightweight real‑time monitor for CPU and
memory usage.  It relies on the `psutil` library to sample system
metrics and displays them as color‑coded bar graphs in the console.  If
the optional `rich` library is installed, future versions could
leverage it for nicer output; however this implementation uses plain
ANSI escape codes and ASCII to remain dependency‑free.

Usage example::

    from src.pulse_monitor import PulseMonitor
    mon = PulseMonitor()
    mon.live_graph(duration=10, interval=1)

This will print CPU and memory utilisation once per second for
ten seconds.

Auto‑run
^^^^^^^^

When used as part of the CipherHub launcher, the Pulse monitor can
automatically start in the background if the user's configuration file
(``~/.cipherhubrc``) contains ``"pulse_autorun": true``.  The
launcher spawns a daemon thread that calls ``live_graph`` without
blocking the main application.  See ``src/cipherhub_launcher.py`` for
details.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from typing import Optional

try:
    import psutil  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "psutil is required for pulse_monitor but is not installed. Please install psutil >= 5.0"
    ) from exc


class PulseMonitor:
    """Monitor CPU and memory usage and display simple graphs."""

    def __init__(self, use_rich: bool = False) -> None:
        # Whether to attempt using rich (not implemented yet)
        self.use_rich = use_rich and self._has_rich()

    def _has_rich(self) -> bool:
        try:
            import rich  # type: ignore  # noqa: F401
            return True
        except ImportError:
            return False

    def _colorize(self, text: str, percent: float) -> str:
        """Return text wrapped in ANSI colour codes based on utilisation."""
        # Choose colour: green <50%, yellow <75%, red otherwise
        if percent < 50:
            colour = "\033[92m"  # bright green
        elif percent < 75:
            colour = "\033[93m"  # yellow
        else:
            colour = "\033[91m"  # red
        reset = "\033[0m"
        return f"{colour}{text}{reset}"

    def _draw_bar(self, percent: float, width: int) -> str:
        bar_len = max(0, min(width, int((percent / 100.0) * width)))
        bar = "█" * bar_len
        pad = " " * (width - bar_len)
        return bar + pad

    def live_graph(self, duration: Optional[float] = None, interval: float = 1.0) -> None:
        """Continuously print CPU and memory usage bars.

        :param duration: Duration in seconds to run the monitor.  If None,
            runs indefinitely until interrupted.
        :param interval: Sampling interval in seconds.
        """
        start = time.time()
        # Determine console width minus label area
        try:
            columns = shutil.get_terminal_size((80, 20)).columns
        except Exception:
            columns = 80
        bar_width = max(10, columns - 20)
        try:
            # Use non-blocking sampling for CPU percent; first call discards previous value
            psutil.cpu_percent(None)
            while True:
                now = time.time()
                if duration is not None and now - start >= duration:
                    break
                cpu = psutil.cpu_percent(None)
                mem = psutil.virtual_memory().percent
                cpu_bar = self._draw_bar(cpu, bar_width)
                mem_bar = self._draw_bar(mem, bar_width)
                cpu_line = f"CPU {cpu:5.1f}% [" + self._colorize(cpu_bar, cpu) + "]"
                mem_line = f"MEM {mem:5.1f}% [" + self._colorize(mem_bar, mem) + "]"
                # Clear screen if possible
                if os.name != "nt":
                    # Move cursor to start of line and clear to end
                    sys.stdout.write("\033[2J\033[H")
                print(cpu_line)
                print(mem_line)
                sys.stdout.flush()
                time.sleep(interval)
        except KeyboardInterrupt:
            pass