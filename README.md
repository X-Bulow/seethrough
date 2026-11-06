# seethrough

**Do Memory-Safety Detectors See Through Custom Allocators?**
CS5439 Assignment 2 — Cheng Zefeng, Wei Yuning, Xu Ruofan. Due 2026-11-19.

Two questions, one table and one set of plots:

- **Q1 Detection.** For the same bug, what does each tool lose when the object comes from a
  custom memory allocator (CMA) instead of `malloc`, and what do the tool's own annotations
  (ASan manual poisoning, Valgrind mempool requests) win back?
- **Q2 Overhead.** What do the tools cost in time and peak memory on real programs that use
  CMAs heavily, with and without annotations?

The professor's feedback and what we do about each point is in
[docs/professor-feedback.md](docs/professor-feedback.md). The task list, one line per task,
is [TASKS.md](TASKS.md).

## Layout

| directory | owner | what lives there |
|---|---|---|
| `corpus/` | A | the test programs. `cases/` holds 16 constructed defects with known ground truth (five classes, read and write forms, plus the variants that isolate one allocator property) and their negative controls; `include/alloc.h` is the unified allocator interface; `controls/` the positive controls; `real/` four real SQLite 3.22.0 defects ported from capstone's engine-repros (Tier 2) |
| `allocators/` | B | one implementation of `alloc.h` per allocator layer: `malloc`, `arena`, `freelist`, `sqlite` (memsys5 / lookaside); `annotations/` holds the ASan and Valgrind annotation macros |
| `harness/` | A | `run-matrix.py` builds and runs tool x allocator x annotation x case and writes one CSV; `run-real.py` does the same for `corpus/real/` over tool x arm; `classify.py` turns a tool's output into a verdict |
| `tools/` | C | compile flags per tool (`flags.mk`), `setup-server.sh` that installs or builds the pinned tool versions on the lab server, `env.sh` that records them |
| `benchmarks/` | C | Q2: SQLite speedtest1, PostgreSQL subset, Lua or CPython |
| `results/` | all | raw outputs and CSVs, one directory per run, never edited by hand |
| `docs/` | all | design notes, the test-program explanations, the environment record |
| `report/` | all | pointer to the Overleaf report; figures regenerated from `results/` |

## The experiment in one sentence

Every case is compiled once per cell of the matrix

    tool       x  allocator  x  annotation  x  case  x  {bug, control}
    asan          malloc        off            7 classes   bug = defect present
    valgrind      arena         on             (x read/     control = same allocation
    hwasan        freelist                      write)      traffic, the invalid
    ubsan         memsys5                                   access replaced
    lowfat        lookaside                                 (x86-64 Linux, the lab server)

and the run is read into one of five verdicts (see below). A tool x allocator cell is only
trusted if the positive control for that tool (plain `malloc` use-after-free and overflow)
was DETECTED in the same run; otherwise the whole cell is TOOL-ERROR, not MISSED.

## Verdicts

| verdict | meaning |
|---|---|
| `DETECTED` | the tool reported the defect, at the right site, and the control image ran clean |
| `MISSED` | the bug image ran to completion with no report, and the control ran clean |
| `FALSE-POSITIVE` | the control image (no defect) produced a report |
| `UNSUPPORTED` | the tool cannot build or run this configuration at all (e.g. HWASan on an x86-64 CPU without LAM) |
| `TOOL-ERROR` | the positive control failed, or the tool crashed: the cell carries no information |
| `CLEAN` | control rows only: the no-defect image ran to completion with no report, as it should |

## Running

    make help                                  # all targets
    make case CASE=heap-overflow-write TOOL=asan ALLOC=malloc ANNOT=0
    make control CASE=heap-overflow-write TOOL=asan ALLOC=arena ANNOT=1
    python3 harness/run-matrix.py --tools asan valgrind --allocs malloc arena --out results/$(date +%F)-local
    python3 harness/run-real.py   --tools asan valgrind --out results/$(date +%F)-local-real   # corpus/real, fetches SQLite 3.22.0 into vendor/

All measured runs happen natively on the lab's x86-64 Linux server, with the tool versions
pinned in `tools/setup-server.sh` and recorded by `tools/env.sh` into every results bundle.
Runs on a laptop (macOS, arm64) are for development only and must not appear in `results/`.

## Conventions we took from the Capstone bug corpora

The layout follows `capstone/bug-corpora` in project-starch/llvm-capstone (dev branch):

- one directory per case, the directory name is metadata (`NN_<class>_<slug>`), numbers dense;
- `case.c` holds the sequence inside `ST_CASE(NN)`; `case.json` holds the machine-readable claims
  (class, access kind, object, expected fault site, per-arm verdicts with `verdict_from`);
- every case has a **negative control** under `-DST_NEGATIVE_CONTROL` that keeps the allocation
  and free traffic byte for byte and replaces only the invalid access;
- every runner executes a **positive control** before any case and exits 75 with no verdict if
  the control is not detected, so an infrastructure failure can never be read as a measurement;
- results are a committed bundle under `results/<date>-<arm>/`, and every verdict in a
  `case.json` names the bundle it came from.
