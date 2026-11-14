# case05-heap-underflow-write — a one-byte write before the start

## Defect
- Class: heap underflow; access: write
- Object: `a`, 24 bytes, allocated after another 24-byte object `first`
- In one line: writes `*(a - 1)`

## Why underflow is separate from overflow
For these tools the two sides of an object are not symmetric:
- a bump-pointer arena's left neighbour is an **earlier** allocation, its right neighbour a later one
- a free list often keeps its own free-list link or header on the left (ours keeps neither in front of a live object; see case 7)
- ASan's left and right redzones are checked by different instrumentation
- **LowFat is more precise for underflow than for overflow**: an object's base is aligned to its region, so anything below the base is out of bounds, while an overflow inside the size class is not. That is why case 5 is reported and case 1 is not

On malloc `*(a-1)` is the last byte of the chunk header, which libc reads back in `free()`, so even without a tool the program may crash later — the `none` column is worth a look.

## Memory layout
```
arena (16-aligned):  [ first: 24 |slack 24..31 ][ a: 24 |slack ]
                                           ^31       ^32
                     *(a-1) is first's last slack byte
                     unannotated: addressable → not reported
                     annotated:   first unpoisoned only 24 bytes → 31 is still poisoned → reported
```

## Expected results
See `case.json`.

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
| hwasan | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. Annotated, `first` and `a` carry different tags.

## Formal results (2026-11-13)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 | memsys5 a0 | memsys5 a1 | lookaside | arena-rewrite | freelist-rewrite |
|---|---|---|---|---|---|---|---|---|---|---|
| asan | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| valgrind | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| hwasan | DETECTED | MISSED | DETECTED | MISSED | DETECTED | — | — | — | — | — |

ASan and Valgrind: lab server, x86-64 (`results/2026-11-13-lab-core`, `-memsys5`, `-lookaside`, `-rewrite`; commit `6b54739`); every bug cell is identical to the EC2 bundles of 2026-11-10. HWASan: aarch64 Lima VM (`results/2026-11-13-lima-hwasan`, commit `c214ad3`); it was not run on the SQLite or rewrite arms. Every negative control was CLEAN. MISSED (SEGV) means the program crashed after READY inside the tool's signal handler, without a report on the defect.
