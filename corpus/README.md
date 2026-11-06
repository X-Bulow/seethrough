# corpus — the test programs (Part A)

One directory per case under `cases/`. A case is three files:

    cases/<class>-<access>/
        case.c       the sequence, inside ST_CASE(NN); the negative control under -DST_NEGATIVE_CONTROL
        case.json    machine-readable claims: class, access, object, offset, expected verdicts, measured verdicts
        README.md    the explanation the professor asked for (template: docs/test-programs.md)

Case numbers are dense (0..N-1) and listed in `cases/INDEX.md`: 16 cases over five classes
(heap overflow, heap underflow, use after free, double free, invalid free), each class in its
read and write form, plus the variants that isolate one property of the allocator -- the
distance of an overflow, whether the storage was reissued, whose lifetime ended. Every case allocates only
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
6. **A case that could not be constructed is not a miss.** Some cases need a property of the
   allocator: that a freed block is reissued (10, 15), that `st_realloc` moves (11), that there
   is a pool at all (12). Each prints a marker and names it in `case.json` `requires`, and
   `harness/run-matrix.py` records a row whose marker is absent as UNSUPPORTED. The property is
   per CELL, not per case: ASan's quarantine stops malloc from reusing a block, so `asan+malloc`
   is UNSUPPORTED for case 10 while `none+malloc` is a real measurement.
7. **The corpus may add to `alloc.h`, but never read an allocator's internals.** Case 4 needs the
   pool's outer boundary, so the interface gained `st_alloc_pool_bytes()`; no case hardcodes a
   size or includes an allocator's header.

## Controls

`controls/` holds the positive controls the harness runs before any case:

- `positive-uaf.c` — plain `malloc` use-after-free read. ASan, Valgrind, HWASan must all DETECT it.
- `positive-overflow.c` — plain `malloc` 1-byte heap overflow write. Same.

If a tool does not detect its positive control, the harness exits 75 and writes no verdicts for
that tool. That is the only way "the tool is broken" and "the tool missed it" stay distinct.
