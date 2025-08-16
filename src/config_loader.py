"""
config_loader.py
----------------

This module provides simple configuration loading for the CipherHub
platform.  It reads a JSON file from ``~/.cipherhubrc`` (or an
explicit path) and returns its contents as a dictionary.  The file
may contain user preferences for CPU affinity, process priority,
automatic flushing or ignition on boot, and whether to auto‑start
the Pulse monitor.

Example ``~/.cipherhubrc``::

    {
      "cpu_cores": [0, 1],
      "priority": -10,
      "flush_on_boot": true,
      "ignite_autorun": true,
      "pulse_autorun": false
    }

Applications should call ``load_cipherhub_config()`` at startup and
interpret the resulting keys according to their needs.  Unknown keys
are preserved so that future releases can introduce additional
configuration options without breaking compatibility.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("cipherhub.config")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def load_cipherhub_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the CipherHub configuration from a JSON file.

    :param path: Optional path to a configuration file.  If not provided
        the function attempts to read ``~/.cipherhubrc``.  If the file
        does not exist or cannot be parsed, an empty dictionary is
        returned.
    :returns: A dictionary of configuration options.
    """
    config_path = path or os.path.expanduser("~/.cipherhubrc")
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            logger.info(f"Loaded CipherHub config from {config_path}: {data}")
            return data
        else:
            logger.warning(f"CipherHub config {config_path} must contain a JSON object")
    except Exception as exc:
        logger.warning(f"Failed to load CipherHub config {config_path}: {exc}")
    return {}