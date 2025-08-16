"""
mnemos
------

This package implements the **MNEMOS** memory kernel for CipherWorks.
MNEMOS provides a modular persistence layer for storing and retrieving
agent state across sessions.  It also offers mechanisms for creating
and re‑binding memory maps and provisioning cross‑agent slots.

The core implementation lives in ``mnemos/core.py``.  Additional
modules provide integration with THRUST (see ``mnemos/thrust_bridge.py``)
and other subsystems within the CipherWorks platform.

Note: MNEMOS is under active development.  The current version
contains stub implementations that will be fleshed out in future
releases.
"""

from .core import MnemosCore  # re-export primary class
from .thrust_bridge import ThrustIntegration
from .thought_bus import ThoughtBus

__all__ = [
    "MnemosCore",
    "ThrustIntegration",
    "ThoughtBus",
]