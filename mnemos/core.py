"""
mnemos.core
----------------

This module defines the core of the **MNEMOS** memory kernel.  MNEMOS
provides persistent thought storage, rebindable memory maps and
cross‑agent slot provisioning.  The design is intentionally modular so
that the underlying storage engine can be swapped out (e.g. JSON
files, SQLite databases, network services) without affecting the
public API.

In this initial version, all operations are implemented in memory and
persisted to a simple JSON file on disk (``~/.mnemos_store.json``).
This allows agents to save and retrieve state across sessions, but is
not intended for production use.  Future versions will support more
robust databases and replication.

Key concepts
^^^^^^^^^^^^

* **Thought**: A serialised representation of an agent's state or
  memory fragment.  Thoughts are keyed by a unique identifier and
  stored persistently.
* **Memory map**: A dictionary mapping slot names to thought IDs.  A
  memory map can be re‑bound at runtime to point to different
  thoughts, enabling dynamic recall and update of agent state.
* **Slot provisioning**: Mechanisms for allocating and sharing
  memory slots across multiple agents.  Slots are named references
  that can be reserved by one agent and used by another.

Example usage:

>>> from mnemos import MnemosCore
>>> mnemos = MnemosCore()
>>> tid = mnemos.store_thought({"hello": "world"})
>>> mnemos.rebind_memory_map("session1", {"greeting": tid})
>>> mnemos.retrieve_thought(tid)
{'hello': 'world'}

"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger("mnemos")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class MnemosCore:
    """Core class for persistent thought storage and memory maps."""

    def __init__(self, store_path: Optional[str] = None) -> None:
        # Determine the on‑disk store file
        self.store_path = store_path or os.path.expanduser("~/.mnemos_store.json")
        self._lock = threading.Lock()
        # In‑memory caches
        self._thoughts: Dict[str, Any] = {}
        self._maps: Dict[str, Dict[str, str]] = {}
        # Load existing data if present
        self._load_store()

    # ------------------------------------------------------------------
    # Persistence layer
    #
    def _load_store(self) -> None:
        """Load persisted thoughts and memory maps from disk."""
        if not os.path.exists(self.store_path):
            return
        try:
            with open(self.store_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                self._thoughts = data.get("thoughts", {})
                self._maps = data.get("maps", {})
                logger.info(f"Loaded MNEMOS store from {self.store_path}")
        except Exception as exc:
            logger.warning(f"Failed to load MNEMOS store: {exc}")

    def _save_store(self) -> None:
        """Persist current thoughts and maps to disk."""
        with self._lock:
            try:
                data = {"thoughts": self._thoughts, "maps": self._maps}
                with open(self.store_path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh)
                logger.info(f"Saved MNEMOS store to {self.store_path}")
            except Exception as exc:
                logger.warning(f"Failed to save MNEMOS store: {exc}")

    # ------------------------------------------------------------------
    # Thought management
    #
    def store_thought(self, obj: Any) -> str:
        """Persist a thought and return its unique identifier.

        :param obj: Any JSON serialisable object representing the thought.
        :returns: A UUID string identifying the stored thought.
        """
        thought_id = str(uuid.uuid4())
        with self._lock:
            self._thoughts[thought_id] = obj
            self._save_store()
        logger.info(f"Stored thought {thought_id}")
        return thought_id

    def retrieve_thought(self, thought_id: str) -> Optional[Any]:
        """Retrieve a previously stored thought by ID.

        :param thought_id: The UUID of the thought to fetch.
        :returns: The stored object or ``None`` if not found.
        """
        return self._thoughts.get(thought_id)

    # ------------------------------------------------------------------
    # Memory maps
    #
    def rebind_memory_map(self, name: str, mapping: Dict[str, str]) -> None:
        """Create or update a memory map.

        Memory maps bind human‑readable slot names to thought IDs.  They
        allow agents to organise their thoughts into named categories and
        update them atomically.

        :param name: The name of the memory map (e.g. session identifier).
        :param mapping: A dictionary mapping slot names to thought IDs.
        """
        with self._lock:
            self._maps[name] = mapping.copy()
            self._save_store()
        logger.info(f"Rebound memory map '{name}' with {len(mapping)} slots")

    def get_memory_map(self, name: str) -> Optional[Dict[str, str]]:
        """Return the memory map for a given name, if present."""
        return self._maps.get(name)

    # ------------------------------------------------------------------
    # Slot provisioning
    #
    def provision_slot(self, map_name: str, slot: str) -> str:
        """Allocate a slot in a memory map and return its current thought.

        If the slot does not exist it will be created with a new empty
        thought.  If the memory map does not exist it will be created as
        well.  Returns the thought ID associated with the slot.

        :param map_name: The memory map name to provision.
        :param slot: The slot name within the map.
        :returns: The thought ID for the slot.
        """
        with self._lock:
            if map_name not in self._maps:
                self._maps[map_name] = {}
            mapping = self._maps[map_name]
            if slot not in mapping:
                # create a new empty thought
                tid = str(uuid.uuid4())
                self._thoughts[tid] = None
                mapping[slot] = tid
                self._save_store()
                logger.info(f"Provisioned new slot '{slot}' in map '{map_name}'")
                return tid
            else:
                return mapping[slot]