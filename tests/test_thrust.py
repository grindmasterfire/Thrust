"""
Basic unit tests for the THRUST open core and Pro module.
Run with a standard Python test runner (e.g. pytest) from the project root:

    pytest -q
"""

import importlib
import pytest


def test_thrust_core_imports() -> None:
    """Ensure the core module can be imported without errors."""
    module = importlib.import_module("src.thrust_core")
    assert hasattr(module, "ThrustCore")


def test_pro_features_without_license() -> None:
    """Pro functions should raise PermissionError when no licence key is present."""
    pro = importlib.import_module("src.pro_features")
    # clear environment variable for licence if present
    import os
    os.environ.pop("THRUST_LICENSE_KEY", None)
    # ensure no rc file interfering
    rc = os.path.expanduser("~/.thrustrc")
    if os.path.exists(rc):
        pytest.skip("User has a local .thrustrc file with a license key, skipping")
    with pytest.raises(PermissionError):
        pro.aggressive_cache_clear()
    # Additional pro functions should also raise without a licence
    with pytest.raises(PermissionError):
        pro.apply_runtime_profile("default")
    with pytest.raises(PermissionError):
        pro.start_background_daemon()