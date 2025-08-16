"""
shield_recovery.py
-------------------

This module implements rudimentary crash recovery for THRUST.  The
``save_state`` function captures a snapshot of the current system
performance and engine configuration and writes it to a JSON file in
``~/.mnemos/last_state.json``.  The ``restore_last_state`` function
attempts to restore CPU affinity and process priority using the
captured snapshot.  These functions are invoked by the CLI on
startup/shutdown to provide a basic form of "safe boot" should the
application terminate unexpectedly.

The snapshot is intentionally simple and does not capture every
possible state.  Future releases may augment the data model and
integrate more tightly with MNEMOS.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

try:
    import psutil  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "psutil is required for shield_recovery but is not installed. Please install psutil >= 5.0"
    ) from exc


# Directory and file used to persist the last known state
LAST_STATE_DIR = os.path.expanduser("~/.mnemos")
LAST_STATE_FILE = os.path.join(LAST_STATE_DIR, "last_state.json")


def save_state(engine: Any) -> None:
    """Persist a snapshot of the current state to disk.

    :param engine: A ``ThrustCore`` instance whose affinity and priority
        should be captured.  Only ``_original_affinity`` and
        ``_original_nice`` are persisted.
    """
    try:
        os.makedirs(LAST_STATE_DIR, exist_ok=True)
        snapshot: Dict[str, Any] = {
            "timestamp": time.time(),
            "cpu_affinity": list(engine._original_affinity) if getattr(engine, "_original_affinity", None) else None,
            "priority": engine._original_nice if getattr(engine, "_original_nice", None) else None,
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "mem_percent": psutil.virtual_memory().percent,
            },
        }
        with open(LAST_STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh)
    except Exception:
        # Best effort; ignore errors
        pass


def restore_last_state(engine: Any) -> None:
    """Restore CPU affinity and process priority from the last snapshot.

    If the snapshot file exists, this function reads the saved
    ``cpu_affinity`` and ``priority`` values and applies them to the
    provided engine.  Errors are ignored.  After restoration the
    snapshot file is deleted to avoid repeated restores.

    :param engine: A ``ThrustCore`` instance on which to call
        ``set_cpu_affinity`` and ``set_priority``.
    """
    if not os.path.exists(LAST_STATE_FILE):
        return
    try:
        with open(LAST_STATE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        affinity = data.get("cpu_affinity")
        priority = data.get("priority")
        if affinity:
            try:
                engine.set_cpu_affinity(affinity)
            except Exception:
                pass
        if priority is not None:
            try:
                engine.set_priority(priority)
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try:
            os.remove(LAST_STATE_FILE)
        except Exception:
            pass