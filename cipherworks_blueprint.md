# CipherWorks Blueprint

This document provides the complete build and maintenance blueprint for the **CipherWorks** AI acceleration suite. The suite enhances local large language model (LLM) runtimes, optimizes system resources, and offers persistent memory interfaces. All components are modular, license‑aware, CLI‑accessible, and documented for both open‑core and Pro editions.

## 🧩 Directory Structure

```
cipherworks/
├── bin/
│   ├── cipher                    # Master CLI launcher
│   ├── wrappers/
│   │   ├── thrust                # Legacy CLI
│   │   └── pro                   # Legacy Pro CLI
├── src/
│   ├── thrust_core.py           # Open‑core runtime optimizer
│   ├── pro_features.py          # Pro‑only runtime boosts
│   ├── mute_cleaner.py          # Memory flusher (MUTE)
│   ├── ignite_launcher.py       # Prefetcher + booster (IGNITE)
│   ├── pulse_monitor.py         # System monitor (PULSE)
│   ├── shield_recovery.py       # Crash restore engine (SHIELD)
│   ├── cipherhub_launcher.py    # Central control logic
│   └── config_loader.py         # Reads `.thrustrc` and `.cipherhubrc`
├── mnemos/
│   ├── __init__.py              # Memory core kernel
│   ├── thrust_bridge.py         # Connects to THRUST Pro features
│   └── thought_bus.py           # Thought persistence & TTL bus
├── docs/
│   └── architecture.md          # Developer architecture map
├── tests/
│   └── test_thrust.py           # Unit tests
├── LICENSE                      # MIT (open‑core)
├── LICENSE_PRO.txt              # Proprietary Pro terms
├── .thrustrc                    # Runtime defaults for THRUST
├── .cipherhubrc                 # Full suite config
└── README.md
```

## 🔧 1. Setup & Dependencies

Before running CipherWorks or its tests, install dependencies:

```bash
pip install psutil
```

Platform‑specific considerations:

- **Linux** – supports `/proc/sys/vm/drop_caches` for aggressive cache flush.
- **Windows** – uses the `EmptyWorkingSet` function via the Windows API for memory flushing.
- **macOS** – requires the `purge` utility for aggressive memory clearing.

## 📦 2. License Gating

CipherWorks follows an open‑core model. The open‑core modules are licensed under MIT, while Pro features require a valid licence key. In `pro_features.py`, gate all Pro methods with:

```python
if not license_key_valid():
    raise PermissionError("Pro features require a valid license.")
```

Acceptable licence locations:

- Environment variable: `THRUST_LICENSE_KEY`
- `~/.thrustrc`
- `~/.cipherhubrc`

## 🔌 3. Core Modules to Expand

### ✅ THRUST

Optimizes local LLM runtimes (e.g., Ollama, LM Studio, GPT4All, Claude CLI). It includes functions to pin processes to CPU cores via `cpu_affinity`, adjust process priority, flush caches, and benchmark scripts. Command‑line interface (`bin/thrust`) includes `auto`, `benchmark`, `boost`, `mute` and supports Pro subcommands.

### ✅ MUTE

A memory cleaning tool with soft and aggressive modes. Functions are implemented in `mute_cleaner.py`:

- `soft_clean()` – triggers Python garbage collection via `gc.collect()`.
- `aggressive_clean()` – performs platform‑specific OS cache clearing.

Accessible via `cipher mute --soft` or `cipher mute --aggressive`.

### ✅ PULSE

Provides a real‑time CPU and memory monitor using `psutil`. It displays a live dashboard in the terminal and can auto‑launch if `pulse_autorun` is set in `.cipherhubrc`. Use `cipher pulse` to run it on demand.

### ✅ IGNITE

Prefetches model files into memory and sets CPU affinity and priority. Implemented in `ignite_launcher.py` and available via `cipher ignite --model /path/to/model.bin`. Supports optional arguments for CPU cores and priority.

### ✅ SHIELD

Implements crash recovery by saving system state to `~/.mnemos/last_state.json` and restoring it at startup if `auto_restore` is true. See `shield_recovery.py`.

### ✅ MNEMOS

Provides persistent memory for AI agents. The `ThoughtBus` class supports:

- Thoughts tagged with TTL (time‑to‑live)
- Memory groups and agent tags
- Persistent storage in `~/.mnemos_bus.json`
- Bridging to THRUST Pro functions via `thrust_bridge.py`

Command `cipher mnemos scan` dumps active thoughts.

### ✅ CIPHER

The unified entry point in `bin/cipher` acts like a git‑style wrapper. It handles subcommands for MUTE, IGNITE, PULSE, SHIELD, and MNEMOS, and proxies legacy THRUST commands via `bin/wrappers/thrust` and `bin/wrappers/pro`. It reads configuration from `.cipherhubrc` and `.thrustrc` to determine default behaviours.

## 📘 4. Documentation

* **README.md** – Describe CLI usage with examples (see [Usage](#8-example-cli-usage)) and provide a feature comparison table (Community vs. Pro). Outline installation steps, dependency requirements, and licence terms. Include a bug‑report or developer contact section.
* **docs/architecture.md** – Diagram the interaction between modules, the license separation, and the bootflow executed by `cipher` when the suite starts. Describe the flow from reading configs, restoring state (SHIELD), prefetching models (IGNITE), cleaning memory (MUTE), launching PULSE monitors, and integrating THRUST and MNEMOS.

## ✅ 5. Unit Testing & Validation

Implement unit tests under `tests/` using `pytest` or `unittest`. Tests should:

- Import and instantiate all modules without error.
- Verify Pro licence enforcement by expecting a `PermissionError` when licence is missing.
- Smoke test CLI entry points for dry runs.

## 🧠 6. Thoughtflow Integration

Future expansions may introduce CircuitNet or Persona Mode. These would allow MNEMOS memory to sync with external AI agents (e.g., ChatGPT, Claude) via `.mnemosrc` configuration. Add a `mnemos sync` CLI command to support portability of memory across environments.

## 🗂️ 7. Release & Maintenance

Release the open‑core under MIT licence on GitHub. Pro binaries or source code may be distributed via PyPI, Gumroad, or through GitHub Pro licence flows. Provide a script (`bin/cipher update`) to check for new versions and automatically update local installations. Developers should generate version bump PRs with changelogs when features are added.

## 🏁 8. Example CLI Usage

```bash
cipher ignite --model ./ggml-model.bin
cipher mute --aggressive
cipher pulse
cipher shield restore
cipher mnemos scan
```

## 🔒 9. Future Plugins (Wish List)

- **LATTICE** – AI plugin manager for model routing.
- **TESSERACT** – Experimental quantum memory compression.
- **CIRCUIT** – Runtime monitor with intelligent profiling.
- **FLARE** – Diagnostic reporter and telemetry (opt‑in).
- **VESSEL** – Portable memory capsule (backup & migrate).

## 🔚 Mission Endpoint

With this blueprint, a developer or AI agent can complete, expand, and maintain the CipherWorks suite. The project is modular, documented, testable, and enforces licence terms for open‑core and Pro features.