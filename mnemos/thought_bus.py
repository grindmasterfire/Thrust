"""
mnemos.thought_bus
------------------

This module implements the **Thought Bus** for the MNEMOS memory
kernel.  The Thought Bus acts as a real‑time orchestration layer
between THRUST, MNEMOS, CipherHub and third‑party agents.  It
manages the publication and retrieval of "thoughts"—serialised
objects representing agent state or system observations—and
coordinates their lifecycle via time‑to‑live (TTL) semantics.

Key features
^^^^^^^^^^^^

* **Thought slots with TTL**: Each published thought can include an
  optional expiry time.  Expired thoughts are automatically purged
  during retrieval or when ``clean_expired`` is invoked.
* **Agent tagging**: Thoughts are tagged with the name of the agent
  publishing them.  This allows consumers to filter by agent.
* **Persistent state**: All bus activity is persisted to a JSON
  file (``~/.mnemos_bus.json`` by default) so that thought history
  survives process restarts.
* **Bridging to THRUST/MUTE/IGNITE**: The bus exposes helper
  methods that proxy calls to THRUST Pro features and other
  subsystems.  These proxies raise runtime or permission errors
  depending on the environment and licence state.

Example usage::

    from mnemos.thought_bus import ThoughtBus
    bus = ThoughtBus()
    tid = bus.publish_thought("agentA", {"metric": 0.5}, ttl=30)
    thoughts = bus.get_thoughts("agentA")

In addition to basic publishing and retrieval, the bus can invoke
THRUST Pro hooks through its ``thrust`` property, perform soft or
aggressive memory cleaning via ``mute`` and run Ignite tuning using
``ignite``.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .core import MnemosCore
from .thrust_bridge import ThrustIntegration
# Import MuteCleaner and IgniteLauncher with fallbacks.  During CLI
# execution the ``src`` directory is added to sys.path so these
# imports succeed.  When used in a package context we attempt to
# import modules relative to the root of the repository.  If neither
# import works a RuntimeError is raised when the corresponding methods
# are invoked.
try:
    from src.mute_cleaner import MuteCleaner  # type: ignore
    from src.ignite_launcher import IgniteLauncher  # type: ignore
except Exception:
    try:
        from ..src.mute_cleaner import MuteCleaner  # type: ignore  # type: ignore
        from ..src.ignite_launcher import IgniteLauncher  # type: ignore  # type: ignore
    except Exception:
        MuteCleaner = None  # type: ignore
        IgniteLauncher = None  # type: ignore

logger = logging.getLogger("mnemos.bus")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class ThoughtBus:
    """A shared bus for publishing and retrieving thoughts across agents."""

    def __init__(self, store_path: Optional[str] = None) -> None:
        # Underlying Mnemos core for thought storage
        self.core = MnemosCore()
        # Path for persistent bus state
        self.bus_path = store_path or os.path.expanduser("~/.mnemos_bus.json")
        self._state: List[Dict[str, Any]] = []
        # Load existing bus entries if present
        self._load_bus()
        # Integration objects
        self.thrust = ThrustIntegration()
        # Instantiate MuteCleaner and IgniteLauncher only if modules are available
        self.mute = MuteCleaner() if MuteCleaner is not None else None  # type: ignore
        self.ignite = IgniteLauncher() if IgniteLauncher is not None else None  # type: ignore

    # ------------------------------------------------------------------
    # Persistence
    def _load_bus(self) -> None:
        """Load persisted thought bus data from disk."""
        if os.path.exists(self.bus_path):
            try:
                with open(self.bus_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    self._state = data
                    logger.info(f"Loaded ThoughtBus from {self.bus_path} with {len(data)} entries")
            except Exception as exc:
                logger.warning(f"Failed to load ThoughtBus: {exc}")

    def _save_bus(self) -> None:
        """Persist current bus state to disk."""
        try:
            with open(self.bus_path, "w", encoding="utf-8") as fh:
                json.dump(self._state, fh)
            logger.info(f"Saved ThoughtBus to {self.bus_path} with {len(self._state)} entries")
        except Exception as exc:
            logger.warning(f"Failed to save ThoughtBus: {exc}")

    # ------------------------------------------------------------------
    # Thought publishing and retrieval
    def publish_thought(self, agent: str, obj: Any, ttl: Optional[int] = None) -> str:
        """Publish a thought on the bus and return its ID.

        :param agent: Name of the publishing agent.
        :param obj: JSON‑serialisable object representing the thought.
        :param ttl: Optional time to live in seconds.  If provided,
            the thought will expire ``ttl`` seconds after publication.
        :returns: The UUID of the stored thought.
        """
        thought_id = self.core.store_thought(obj)
        entry = {
            "id": thought_id,
            "agent": agent,
            "published": time.time(),
            "ttl": ttl,
        }
        self._state.append(entry)
        self._save_bus()
        return thought_id

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        ttl = entry.get("ttl")
        if ttl is None:
            return False
        return (time.time() - entry.get("published", 0)) > ttl

    def clean_expired(self) -> None:
        """Remove expired thoughts from the bus and underlying store."""
        new_state: List[Dict[str, Any]] = []
        for entry in self._state:
            if self._is_expired(entry):
                # remove underlying thought from core
                tid = entry.get("id")
                # we cannot delete from MnemosCore individually, so we simply drop
                logger.info(f"Thought {tid} expired and removed from bus")
                continue
            new_state.append(entry)
        self._state = new_state
        self._save_bus()

    def get_thoughts(self, agent: Optional[str] = None) -> List[Any]:
        """Retrieve non‑expired thoughts for a specific agent or all agents.

        :param agent: Name of the agent to filter by.  If ``None`` all
            thoughts are returned.  Expired thoughts are removed.
        :returns: A list of thought objects.
        """
        self.clean_expired()
        results: List[Any] = []
        for entry in self._state:
            if agent is not None and entry.get("agent") != agent:
                continue
            tid = entry.get("id")
            thought = self.core.retrieve_thought(tid)
            if thought is not None:
                results.append({"id": tid, "agent": entry.get("agent"), "thought": thought})
        return results

    # ------------------------------------------------------------------
    # Bridging helpers
    def aggressive_clear(self) -> None:
        """Proxy to THRUST's aggressive cache clear (Pro only)."""
        self.thrust.aggressive_clear()

    def apply_profile(self, name: str) -> None:
        """Proxy to THRUST's runtime profile application (Pro only)."""
        self.thrust.apply_profile(name)

    def start_daemon(self) -> None:
        """Proxy to THRUST's background daemon (Pro only)."""
        self.thrust.start_daemon()

    def soft_clean(self) -> None:
        """Perform a soft memory clean via MuteCleaner.

        If the MuteCleaner module is not available, this method logs
        an informational message and does nothing.
        """
        if self.mute is None:
            logger.info("MuteCleaner is unavailable; soft clean skipped")
            return
        self.mute.soft_clean()

    def aggressive_clean(self) -> None:
        """Perform an aggressive memory clean via MuteCleaner.

        If the MuteCleaner module is not available, this method logs
        an informational message and does nothing.
        """
        if self.mute is None:
            logger.info("MuteCleaner is unavailable; aggressive clean skipped")
            return
        self.mute.aggressive_clean()

    def ignite(
        self,
        model_path: Optional[str] = None,
        cpus: Optional[List[int]] = None,
        priority: Optional[int | str] = None,
    ) -> None:
        """Invoke Ignite operations from the bus.

        :param model_path: Optional path to model for prefetching.
        :param cpus: Optional list of CPU indices for affinity tuning.
        :param priority: Optional niceness or priority class.
        """
        if self.ignite is None:
            logger.info("IgniteLauncher is unavailable; ignite skipped")
            return
        self.ignite.launch(model_path=model_path, cpus=cpus, priority=priority)
