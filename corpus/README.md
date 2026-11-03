# corpus — the test programs (Part A)

One directory per case under `cases/`. A case is three files:

    cases/<class>-<access>/
        case.c       the sequence, inside ST_CASE(NN); the negative control under -DST_NEGATIVE_CONTROL
        case.json    machine-readable claims: class, access, object, offset, expected verdicts, measured verdicts
        README.md    the explanation the professor asked for (template: docs/test-programs.md)

Case numbers are dense (0..N-1) and listed in `cases/INDEX.md`. Every case allocates only
through `include/alloc.h`, never through `malloc` directly, so the same source builds against
every allocator layer in `allocators/`.

## Rules (copied from the Capstone corpus contract, trimmed to what we need)

1. **Allocation traffic is the case.** The control image must make exactly the same
   `st_alloc` / `st_free` calls in the same order with the same sizes; it replaces only the
   invalid access. A tool that reports on the control is FALSE-POSITIVE for the whole cell.
2. **Mark before the defect.** `ST_READY()` prints a line right before the invalid access, so a
   run that crashes earlier is TOOL-ERROR (never reached), not DETECTED.
3. **Defeat the optimiser honestly.** Values read by the defect go through `st_sink()`; cases
   are built at `-O0 -g` for detection. If a case is also run at `-O2` the README says so.
4. **One defect per case.** Reads and writes are separate cases, even of the same bug class.
5. **Expected verdicts are written before the run**, in `case.json` `expected`, with a reason.
   Measured verdicts go in `measured`, each naming the `results/` bundle it came from.

## Controls

`controls/` holds the positive controls the harness runs before any case:

- `positive-uaf.c` — plain `malloc` use-after-free read. ASan, Valgrind, HWASan must all DETECT it.
- `positive-overflow.c` — plain `malloc` 1-byte heap overflow write. Same.

If a tool does not detect its positive control, the harness exits 75 and writes no verdicts for
that tool. That is the only way "the tool is broken" and "the tool missed it" stay distinct.
