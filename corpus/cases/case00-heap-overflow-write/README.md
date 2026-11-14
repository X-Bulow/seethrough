# case00-heap-overflow-write — a one-byte write past the end

## Defect
- Class: heap overflow; access: write
- Object: `a`, a 24-byte request, the first of two consecutive `st_alloc(24)` calls
- In one line: writes `a[24]`, one byte past the end of the request

## Trigger
```
a = st_alloc(24);  b = st_alloc(24);
memset(a, 0x5a, 24);  memset(b, 0x5a, 24);
ST_READY();
a[24] = 1;              // the defect
```
The control replaces this line with `a[23] = 1` (the last valid byte); allocation and freeing are identical.

## Memory layout
```
malloc + ASan:   [left redzone ≥16][ a: 24 ][right redzone ≥16] ... [left redzone][ b: 24 ]...
                 a[24] lands in the right redzone, whose shadow marks it unaddressable → reported

arena (16-aligned):  [ a: 24 | slack 8 ][ b: 24 | slack 8 ][ ... ]
                 offset:  0      24  32            56  64
                 a[24] lands in a's own alignment slack (24..31), not in b's data
                 unannotated: to ASan the whole arena is one live object → not reported
                 annotated:   the arena unpoisons only 24 bytes per object, 24..31 stay poisoned → reported
```
**What lets annotation win this row back is the alignment slack.** If the overflow landed exactly on `b[0]` (offset 32), it would hit a byte of a live object, which has to be unpoisoned, and annotation would be powerless — that is what case 3 measures.

## Expected results
See `expected` in `case.json`. The main points:
- ASan remembers the **requested size**, so offset 24 is reported on malloc and on the annotated arena
- LowFat's bound is the **size class** (24 → 32), so offset 24 is in bounds and not reported even on malloc. This is LowFat's known sub-object precision limit, not something the CMA causes; compare case 3
- UBSan needs a static array bound, and a pointer returned by an allocator has none → nothing is reported in any column

## Local smoke run (2026-11-05, macOS arm64, Apple clang 21, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED **use-after-poison** |
| none | MISSED | MISSED | MISSED |

Note that on the annotated arena ASan reports `use-after-poison`, not `heap-buffer-overflow`: the verdict is the same, the **kind** of report differs. The report's tables and any script that counts by keyword need to know this.

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
