# THRUST

THRUST is an experimental cross‑platform accelerator designed to boost the
performance of local large‑language model (LLM) runtimes such as
GPT4All, Claude CLI, Mistral, Ollama and LM Studio.  It works by
adjusting low‑level operating system parameters like CPU affinity,
process priority and memory caching.  THRUST can also prefetch model
files to prime the disk cache and includes an optional benchmark mode.

> **Disclaimer:**  THRUST attempts to optimise resource usage on your
> system.  Some features (such as lowering the nice value or dropping
> kernel caches) may require administrative privileges.  Use with
> caution and monitor your system’s behaviour.

## Features

* **CPU Affinity:**  Pin the Python process or detected AI runtimes to
  a subset of CPU cores to improve cache locality and reduce context
  switching.  Under the hood THRUST uses `psutil.Process().cpu_affinity()` on
  platforms that support it or falls back to `os.sched_setaffinity()` on
  Linux/Unix.

* **Process Priority:**  Elevate the niceness/priority of the current
  process or external runtimes.  On Windows this maps to the appropriate
  priority class (e.g. `HIGH_PRIORITY_CLASS`), while on POSIX systems a
  negative nice value yields higher priority.

* **Memory Flushing:**  Reclaim Python objects via `gc.collect()` and,
  when run in `--aggressive` mode, clear OS caches.  On Linux this writes
  `3` to `/proc/sys/vm/drop_caches` to drop pagecache, dentries and inode
  caches.  On Windows it calls the `EmptyWorkingSet` function through
  `ctypes` and on macOS it invokes the `purge` utility if available.

* **Prefetching:**  Read a model file into memory to warm up disk
  caches.  This can eliminate the initial cold start cost when
  performing the first inference.

* **Runtime Detection:**  Scan the process table for well‑known local
  LLM runtimes (Ollama, LM Studio, GPT4All, etc.) and automatically
  apply affinity and priority boosts.

* **Benchmark Mode:**  Execute any command a configurable number of
  times and report elapsed time per run along with the average.  This
  helps quantify the impact of THRUST settings on inference latency.

* **Configurable:**  Read options from a JSON configuration file
  (`.thrustrc`) to persist preferred settings like default cores,
  niceness or aggressive flushing.

## Editions

THRUST is available in two editions: **Community** (open source under
MIT) and **Pro** (commercial).  The Community edition provides the
core acceleration features and is suitable for most personal use cases.
The Pro edition unlocks additional capabilities designed for
enterprise and power users.  The table below summarises the
differences between the editions:

| Feature                 | Community | Pro |
|-------------------------|-----------|-----|
| CPU Boosting            | ✅         | ✅   |
| Memory Flush            | ✅         | ✅   |
| Aggressive Cache Clear  | ❌         | ✅   |
| Runtime Profiles        | ❌         | ✅   |
| Background Daemon       | ❌         | ✅   |

Pro features are accessed via the `pro` subcommand of the CLI and
require a valid licence key.  Set the `THRUST_LICENSE_KEY` environment
variable or add a `"license_key"` entry to your `~/.thrustrc`
configuration file to enable them.  Without a licence the Pro
commands will raise a `PermissionError`.

## Installation

THRUST is currently a development prototype distributed as source.  To
install the required dependencies clone this repository and ensure that
the `psutil` package is available:

```bash
git clone <repo>
cd <repo>
pip install psutil
```

On Windows the `ctypes` module from the standard library is used to
call `EmptyWorkingSet`; no additional dependencies are required.

## Usage

All functionality is exposed via the `bin/thrust` script.  Use
`--help` to see a list of subcommands and options:

```bash
bin/thrust --help

usage: THRUST – local AI inference accelerator [-h] {benchmark,auto,mute,prefetch,config,boost} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  benchmark             run a command several times and report durations
  auto                  auto detect running LLM runtimes and boost them
  mute                  free system memory and caches
  prefetch              prefetch a model file into cache
  config                load a JSON configuration file
  boost                 boost the current process's affinity and priority

  pro                   invoke Pro edition features (requires licence)
```

### Benchmark

Run an arbitrary command and report execution time for each run:

```bash
bin/thrust benchmark "python demo.py" --runs 3
```

### Auto detect and boost

Search for running LLM runtimes and apply a two‑core affinity and
increased priority:

```bash
bin/thrust auto --cpus 0 1
```

### Free memory (MUTE)

Collect garbage and drop OS caches (requires appropriate privileges):

```bash
bin/thrust mute --aggressive
```

### Prefetch a model file

Warm up caches by reading a model file into memory:

```bash
bin/thrust prefetch /path/to/ggml-model.bin
```

### Load configuration

Load custom settings from a JSON configuration file and merge them into
the active engine:

```bash
bin/thrust config ~/.thrustrc
```

### Manual boost

Manually adjust the current process’s affinity and priority.  The
following pins the process to CPUs 0 and 1 and lowers the nice value
(higher priority):

```bash
bin/thrust boost --cpus 0 1 --nice -10
```

## Development

The core library lives in `src/thrust_core.py` and exposes a
`ThrustCore` class that can be used programmatically.  See the inline
docstrings for details.  Additional subcommands and features are
welcome – the project is intended to evolve into a modular acceleration
layer for the upcoming MNEMOS memory kernel.

## MNEMOS Memory Kernel

MNEMOS is a companion project to THRUST that provides persistent
thought storage, rebindable memory maps and cross‑agent slot
provisioning.  It is implemented in the `mnemos` package.  The core
interface is exposed through the `MnemosCore` class, which allows
agents to store and retrieve JSON‑serialisable data across sessions.
Memory maps can be re‑bound at runtime to adjust which thoughts are
associated with specific slots.  MNEMOS also integrates with THRUST
via the `mnemos.thrust_bridge` module, exposing Pro hooks for
aggressive cache clearing, runtime profiles and background daemons.

To create a persistent thought and assign it to a memory map:

```python
from mnemos import MnemosCore
mnemos = MnemosCore()
tid = mnemos.store_thought({"context": "example"})
mnemos.rebind_memory_map("demo", {"slot1": tid})
```

The MNEMOS APIs are stubs and will be expanded in future releases.

## CipherWorks Hub

The CipherWorks Hub is a forthcoming launcher application that
consolidates THRUST, MNEMOS and other subsystems (PULSE for
telemetry, SHIELD for recovery, IGNITE for tuning and MUTE for
pruning) into a single interface.  The Hub will provide visual
heatmaps of memory usage, safe‑boot recovery, automated inference
tuning and memory management tools.  Stub implementations of these
components live under the `cipherhub` package and document the
anticipated interfaces.

## License

This project is released under the MIT License.  See the `LICENSE`
file for details.