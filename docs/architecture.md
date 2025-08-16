# THRUST Architecture

THRUST is designed around a modular, dual‑licensing model that separates
community and proprietary functionality.  The open‑source core provides
basic system tuning hooks, while the Pro edition adds advanced runtime
profiles, background daemons and aggressive cache management.

## Open Core

The open core consists of the `ThrustCore` class in `src/thrust_core.py`
and the command‑line wrapper in `bin/thrust`.  It exposes the
following capabilities:

* Adjust CPU affinity and process niceness on Linux, Windows and macOS.
* Prefetch model files to warm up OS caches.
* Flush memory via garbage collection and optional page cache clearing.
* Detect running LLM processes and boost them.

All open core functions are released under the MIT license (see
`LICENSE`).

## Pro Features

The Pro edition builds on the open core by introducing:

* **Aggressive cache clearing:**  Platform specific routines that
  aggressively reclaim memory beyond the standard flush.
* **Runtime profiles:**  Named presets that encapsulate affinity,
  priority and cache settings for different environments.
* **Background daemon:**  A long‑running thread that monitors system
  resources and triggers optimisations automatically.

These features live in `src/pro_features.py` and are gated behind a
license check.  A valid licence key must be present in the
`THRUST_LICENSE_KEY` environment variable or in the `.thrustrc` file.
Without a key, calls to Pro functions will raise a
`PermissionError`.

## Configuration

Users can supply a JSON configuration file (`.thrustrc`) either in
their home directory or in the current working directory.  The
configuration may specify the default CPU cores, priority, whether to
run aggressive flushes and the licence key for enabling Pro features.

## Testing

Unit tests live under `tests/`.  A basic test (`test_thrust.py`) is
provided to ensure the open core imports and that Pro features are
properly gated when no licence is present.  Additional tests can be
added as functionality grows.