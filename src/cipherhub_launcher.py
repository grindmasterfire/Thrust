"""
cipherhub_launcher.py
---------------------

This module provides a high‑level interface for bootstrapping and
running the various CipherHub subsystems (THRUST, MNEMOS, MUTE,
PULSE, IGNITE and SHIELD).  It combines configuration loading,
automatic feature activation and simple wrapper methods for
performing common actions.  Applications can instantiate a
``CipherHubLauncher`` to centralise initialisation logic and to
delegate commands to the appropriate engine or subsystem.

Key behaviours
^^^^^^^^^^^^^^

* On initialisation, the launcher loads ``~/.cipherhubrc`` via
  ``load_cipherhub_config``.  If ``flush_on_boot`` is true it
  performs a soft clean via ``MuteCleaner`` to reclaim memory.  If
  ``ignite_autorun`` is true it invokes ``IgniteLauncher`` to
  prefetch the default model (from ``model`` in config) and set
  affinity/priority if specified.  If ``pulse_autorun`` is true it
  spawns a background thread running ``PulseMonitor.live_graph``.
* Provides ``run_ignite``, ``run_mute``, ``run_pulse``, ``restore``
  and ``mnemos_scan`` methods for use by the ``bin/cipher`` CLI.
* Exposes the underlying subsystems as attributes: ``ignite``,
  ``mute``, ``pulse``, ``shield`` and ``mnemos``.

This launcher is distinct from the ``cipherhub.launcher`` package
stub in that it integrates the actual THRUST core components located
in the ``src`` directory and the MNEMOS thought bus.  It is used by
the unified ``cipher`` command line entry point.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Iterable, Optional

# Attempt relative imports first (when part of a package) and fall back to
# absolute imports when this module is executed as a top‑level script.
try:
    from .config_loader import load_cipherhub_config  # type: ignore
    from .ignite_launcher import IgniteLauncher  # type: ignore
    from .mute_cleaner import MuteCleaner  # type: ignore
    from .pulse_monitor import PulseMonitor  # type: ignore
    from .shield_recovery import restore_last_state, save_state  # type: ignore
    from .thrust_core import ThrustCore  # type: ignore
except Exception:
    from config_loader import load_cipherhub_config  # type: ignore
    from ignite_launcher import IgniteLauncher  # type: ignore
    from mute_cleaner import MuteCleaner  # type: ignore
    from pulse_monitor import PulseMonitor  # type: ignore
    from shield_recovery import restore_last_state, save_state  # type: ignore
    from thrust_core import ThrustCore  # type: ignore
from mnemos import ThoughtBus

logger = logging.getLogger("cipherhub.launcher")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class CipherHubLauncher:
    """Launch and manage the core CipherHub services."""

    def __init__(self, config: Optional[dict] = None) -> None:
        # Load configuration on startup
        self.config = config or load_cipherhub_config()
        # Create a common ThrustCore engine used by Mute and Ignite
        self.engine = ThrustCore()
        # Underlying subsystems
        self.ignite = IgniteLauncher(self.engine)
        self.mute = MuteCleaner(self.engine)
        self.pulse = PulseMonitor()
        self.mnemos = ThoughtBus()
        # Perform safe boot restore
        try:
            restore_last_state(self.engine)
        except Exception:
            pass
        # Apply auto actions based on config
        self._apply_config()

    # ------------------------------------------------------------------
    # Configuration driven startup
    def _apply_config(self) -> None:
        """Interpret configuration options and trigger auto actions."""
        cfg = self.config or {}
        # Flush on boot
        if cfg.get("flush_on_boot"):
            logger.info("Flush on boot enabled; performing soft clean")
            try:
                self.mute.soft_clean()
            except Exception as exc:
                logger.warning(f"Failed to perform flush on boot: {exc}")
        # Ignite autorun
        if cfg.get("ignite_autorun"):
            logger.info("Ignite autorun enabled; performing ignite sequence")
            model = cfg.get("model")
            cpus: Optional[Iterable[int]] = cfg.get("cpu_cores")  # type: ignore
            prio: Optional[int | str] = cfg.get("priority")  # type: ignore
            try:
                self.ignite.launch(model_path=model, cpus=cpus, priority=prio)
            except Exception as exc:
                logger.warning(f"Failed to perform ignite autorun: {exc}")
        # Pulse autorun
        if cfg.get("pulse_autorun"):
            logger.info("Pulse autorun enabled; starting background monitor")
            try:
                # Spawn a daemon thread to run live_graph indefinitely
                thread = threading.Thread(
                    target=self.pulse.live_graph,
                    kwargs={"duration": None, "interval": 1.0},
                    daemon=True,
                    name="PulseAutoThread",
                )
                thread.start()
            except Exception as exc:
                logger.warning(f"Failed to start pulse autorun thread: {exc}")

    # ------------------------------------------------------------------
    # Public actions used by the CLI
    def run_ignite(
        self,
        model: Optional[str] = None,
        cpus: Optional[Iterable[int]] = None,
        priority: Optional[int | str] = None,
    ) -> None:
        """Manually trigger the Ignite sequence."""
        self.ignite.launch(model_path=model, cpus=cpus, priority=priority)

    def run_mute(self, aggressive: bool = False) -> None:
        """Run the mute cleaner in soft or aggressive mode."""
        # Save state before performing memory flush operations
        try:
            save_state(self.engine)
        except Exception:
            pass
        if aggressive:
            self.mute.aggressive_clean()
        else:
            self.mute.soft_clean()

    def run_pulse(self, duration: Optional[float] = None, interval: float = 1.0, use_rich: bool = False) -> None:
        """Launch the live pulse monitor interactively."""
        mon = PulseMonitor(use_rich=use_rich)
        mon.live_graph(duration=duration, interval=interval)

    def restore(self) -> None:
        """Restore state from the last SHIELD snapshot."""
        try:
            restore_last_state(self.engine)
        except Exception as exc:
            logger.warning(f"Failed to restore last state: {exc}")

    def mnemos_scan(self, agent: Optional[str] = None) -> list[dict[str, Any]]:
        """Return current thoughts from the MNEMOS bus."""
        try:
            return self.mnemos.get_thoughts(agent)
        except Exception as exc:
            logger.warning(f"Failed to scan mnemos bus: {exc}")
            return []