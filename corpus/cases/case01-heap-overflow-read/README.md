# case01-heap-overflow-read — a one-byte read past the end

## Defect
- Class: heap overflow; access: read
- Object: `a`, 24 bytes, the first of two consecutive `st_alloc(24)` calls
- In one line: reads `a[24]`, one byte past the end of the request

## Trigger
The same allocation sequence as case 0; the defect line is `st_sink(a[24])`, and the control reads `a[23]`.

## Why a read gets its own case
Rule 4 in `corpus/README.md`: reads and writes are separate cases. The reason is not formalism:
- an out-of-bounds **read** corrupts nothing, so nothing will ever crash because of it later; there is no "late evidence"
- Valgrind reports an invalid read only when the byte is **unaddressable**, and inside an arena every byte is addressable
- ASan instruments reads and writes separately, so one can be caught while the other is missed

Under an arena the read also quietly returns whatever byte sits in a's slack, so the program cannot notice either.

## Memory layout
As case 0: `a[24]` lands inside a's 16-byte alignment slack (24..31), not in b's data.

## Expected results
As case 0 (see `case.json`). LowFat does not report even on malloc, because 24 is inside the 32-byte size class.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED |

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

The two free-list columns agree with the two arena columns.

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | DETECTED tag-mismatch | MISSED | MISSED | MISSED | MISSED |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. The annotated columns stay MISSED: the tag covers a's whole second granule, so offset 24 is 16-byte-precise slack that annotated ASan, unpoisoning exactly 24 bytes, does not have.

## Formal results (2026-11-13)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 | memsys5 a0 | memsys5 a1 | lookaside | arena-rewrite | freelist-rewrite |
|---|---|---|---|---|---|---|---|---|---|---|
| asan | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| valgrind | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| hwasan | DETECTED | MISSED | MISSED | MISSED | MISSED | — | — | — | — | — |

ASan and Valgrind: lab server, x86-64 (`results/2026-11-13-lab-core`, `-memsys5`, `-lookaside`, `-rewrite`; commit `6b54739`); every bug cell is identical to the EC2 bundles of 2026-11-10. HWASan: aarch64 Lima VM (`results/2026-11-13-lima-hwasan`, commit `c214ad3`); it was not run on the SQLite or rewrite arms. Every negative control was CLEAN. MISSED (SEGV) means the program crashed after READY inside the tool's signal handler, without a report on the defect.
