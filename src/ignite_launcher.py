"""
ignite_launcher.py
------------------

This module implements the **IGNITE** prefetch and boot tuning engine for
THRUST.  IGNITE provides a simple entry point for warming up model
files, setting CPU affinity and adjusting process priority before an
inference session begins.  It is designed to be invoked either from
the command line (see ``bin/thrust ignite``) or programmatically by
other modules (e.g. MNEMOS or CipherHub).

Key features
^^^^^^^^^^^^

* **Model prefetching**: Read a model file into memory in order to
  populate the OS page cache.  This can reduce cold‑start latency.
* **Affinity tuning**: Pin the process to a subset of CPU cores for
  better cache locality and reduced context switching.
* **Priority adjustment**: Raise the niceness or priority class so
  that inference work receives more CPU time.

Example usage::

    from src.ignite_launcher import IgniteLauncher
    ignite = IgniteLauncher()
    ignite.launch(model_path="/models/ggml.bin", cpus=[0,1], priority=-10)

This will prefetch the specified model, bind the current process to
cores 0 and 1 and set its niceness to -10 (or ``HIGH_PRIORITY_CLASS``
on Windows).  All operations are optional; pass ``None`` to leave
the corresponding parameter unchanged.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

# Import ThrustCore either relative to this package (when used as part of
# the ``src`` package) or from the top‑level module (when ``src`` is
# added to ``sys.path``).  The relative import may fail if the module
# is executed outside of a package context.
try:
    from .thrust_core import ThrustCore  # type: ignore
except Exception:
    from thrust_core import ThrustCore  # type: ignore

logger = logging.getLogger("thrust.ignite")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class IgniteLauncher:
    """Launch prefetch and tuning operations for THRUST.

    This class wraps a ``ThrustCore`` instance and exposes a
    high‑level ``launch`` method that performs optional model
    prefetching, CPU affinity setting and process priority
    adjustment.  Arguments that are ``None`` are ignored, allowing
    callers to selectively enable features.
    """

    def __init__(self, engine: Optional[ThrustCore] = None) -> None:
        self.engine = engine or ThrustCore()

    def launch(
        self,
        model_path: Optional[str] = None,
        cpus: Optional[Iterable[int]] = None,
        priority: Optional[int | str] = None,
    ) -> None:
        """Execute the IGNITE sequence.

        :param model_path: Path to a model file to prefetch.  If
            ``None`` no prefetching occurs.
        :param cpus: Iterable of CPU indices to bind the process to.
            ``None`` leaves affinity unchanged.
        :param priority: Niceness or priority class to set.  Can be
            ``None`` to retain the current priority.  For Windows the
            value may be a ``psutil`` constant (e.g. ``HIGH_PRIORITY_CLASS``).
        """
        # Prefetch model if requested
        if model_path:
            elapsed = self.engine.prefetch_model(model_path)
            if elapsed is not None:
                logger.info(f"Ignite: prefetched model in {elapsed:.2f} seconds")
        # Set CPU affinity
        if cpus is not None:
            self.engine.set_cpu_affinity(cpus)
        # Set priority
        if priority is not None:
            self.engine.set_priority(priority)
        logger.info("Ignite launch completed")