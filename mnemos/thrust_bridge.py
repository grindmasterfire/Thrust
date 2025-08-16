"""
mnemos.thrust_bridge
--------------------

This module provides a thin integration layer between the MNEMOS
memory kernel and the THRUST accelerator.  It allows MNEMOS to
invoke THRUST's Pro features—such as aggressive cache clearing,
runtime profiles and background daemons—without the MNEMOS core
depending directly on THRUST's internal APIs.

The bridge functions proxy calls to ``src/pro_features.py``.  They
will raise ``PermissionError`` if no valid licence key is configured.
Applications using MNEMOS can catch those exceptions to provide
graceful degradation when running without a Pro licence.

Example:

>>> from mnemos.thrust_bridge import ThrustIntegration
>>> thrust = ThrustIntegration()
>>> try:
...     thrust.aggressive_clear()
... except PermissionError:
...     print("Pro licence required for aggressive clear")
"""

from __future__ import annotations

from typing import Any

# Attempt to import pro features.  We try both a top‑level module name
# (for CLI usage where src/ is injected into sys.path) and a module
# inside the ``src`` package.  If neither import works the variables
# will remain ``None`` and calls will raise RuntimeError.
aggressive_cache_clear = None  # type: ignore
apply_runtime_profile = None  # type: ignore
start_background_daemon = None  # type: ignore
try:
    from pro_features import (
        aggressive_cache_clear as _clear,
        apply_runtime_profile as _apply,
        start_background_daemon as _daemon,
    )  # type: ignore
    aggressive_cache_clear = _clear  # type: ignore
    apply_runtime_profile = _apply  # type: ignore
    start_background_daemon = _daemon  # type: ignore
except Exception:
    try:
        from src.pro_features import (
            aggressive_cache_clear as _clear,
            apply_runtime_profile as _apply,
            start_background_daemon as _daemon,
        )  # type: ignore
        aggressive_cache_clear = _clear  # type: ignore
        apply_runtime_profile = _apply  # type: ignore
        start_background_daemon = _daemon  # type: ignore
    except Exception:
        pass


class ThrustIntegration:
    """Expose THRUST Pro hooks as callable methods within MNEMOS."""

    def aggressive_clear(self) -> None:
        """Invoke the aggressive cache clear feature (Pro only)."""
        if aggressive_cache_clear is None:
            raise RuntimeError("THRUST pro_features module not available")
        aggressive_cache_clear()  # type: ignore[operator-not-callable]

    def apply_profile(self, name: str) -> None:
        """Apply a runtime profile by name (Pro only).

        :param name: The name of the profile to apply.
        """
        if apply_runtime_profile is None:
            raise RuntimeError("THRUST pro_features module not available")
        apply_runtime_profile(name)  # type: ignore[operator-not-callable]

    def start_daemon(self) -> None:
        """Start the background performance daemon (Pro only)."""
        if start_background_daemon is None:
            raise RuntimeError("THRUST pro_features module not available")
        start_background_daemon()  # type: ignore[operator-not-callable]