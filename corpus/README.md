# Test corpus

Constructed defects isolate allocator behavior; real SQLite defects test how those observations transfer to an application.

- [cases/INDEX.md](cases/INDEX.md) — 16 constructed defects with paired controls
- [controls/positive-overflow.c](controls/positive-overflow.c) and [controls/positive-uaf.c](controls/positive-uaf.c) — detector checks
- [real](real/README.md) — four real SQLite defects
- [include/alloc.h](include/alloc.h) — shared allocator interface
- [include/harness.h](include/harness.h) — case macros and execution markers

Each case has `case.c` for the trigger and `case.json` for expectations and measurements. Run cases using the [harness](../harness/README.md).
