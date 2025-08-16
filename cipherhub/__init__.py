"""
cipherhub
---------

This package contains the top‑level launcher and UI components for
CipherWorks Hub, an integrated control centre for the THRUST and
MNEMOS systems.  The Hub will eventually provide graphical and
command‑line interfaces for monitoring system performance, tuning
inference settings and managing persistent agent state.

Currently the submodules are stubs.  They define the interfaces
expected by the larger application but do not implement actual
functionality.  Future releases will flesh out these components.
"""

from .launcher import CipherHubLauncher  # re-export launcher class

__all__ = ["CipherHubLauncher"]