"""
pro_features.py
----------------

This module exposes the commercial capabilities of THRUST.  Certain
optimisations—such as aggressive cache clearing, runtime profiles and
background daemons—are only available in the Pro edition.  A valid
licence key must be provided at runtime (e.g. via the `.thrustrc`
file or an environment variable) to enable these functions.

The functions in this module perform runtime license checks and
either execute the requested operation or raise a ``PermissionError``
if no valid licence is found.
"""

import os
import logging
import json

logger = logging.getLogger("thrust.pro")


def _load_license_key() -> str | None:
    """Load the licence key from the environment or the .thrustrc file.

    The Pro edition checks for a licence in the ``THRUST_LICENSE_KEY``
    environment variable first.  If not found it attempts to parse
    ``~/.thrustrc`` (JSON) for a ``license_key`` entry.  Returns
    ``None`` if no licence is configured.
    """
    key = os.environ.get("THRUST_LICENSE_KEY")
    if key:
        return key
    # fall back to user's home rc
    rc_path = os.path.expanduser("~/.thrustrc")
    try:
        with open(rc_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data.get("license_key")
    except Exception:
        return None
    return None


def _check_license() -> None:
    """Verify that a licence key is present.

    Raises ``PermissionError`` if no key is configured.  The actual
    validation of the key (e.g. contacting a licence server) would be
    implemented in a future release.
    """
    key = _load_license_key()
    if not key or key == "ENTER-YOUR-LICENSE-KEY-HERE":
        raise PermissionError(
            "Pro feature requires a valid THRUST licence. Set THRUST_LICENSE_KEY or update .thrustrc"
        )


def aggressive_cache_clear() -> None:
    """Clear OS caches more aggressively.

    This Pro feature may call platform specific commands that go beyond
    the open core's flush_memory implementation, such as dropping
    free lists or performing additional synchronisation.  Currently it
    emits a log message indicating that the cache would be cleared.
    """
    _check_license()
    logger.info("Aggressive cache clear invoked (stub)")
    # Real implementation would go here


def start_background_daemon() -> None:
    """Start a low‑priority background thread to perform upkeep.

    The Pro edition can run a background daemon that monitors system
    resources and automatically triggers memory flushes or affinity
    adjustments.  In this stub version we merely log the action.
    """
    _check_license()
    logger.info("Background daemon would start here (stub)")


def apply_runtime_profile(profile_name: str) -> None:
    """Apply a runtime tuning profile.

    A runtime profile encapsulates a set of affinity, priority and
    caching settings optimised for a specific environment (e.g.
    laptops, desktops, servers).  Profiles are stored in a Pro
    database.  This stub logs the requested profile name after
    verifying the licence.

    :param profile_name: Name of the profile to apply.
    """
    _check_license()
    logger.info(f"Applying runtime profile '{profile_name}' (stub)")