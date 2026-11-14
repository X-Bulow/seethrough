# case02-heap-overflow-write-slack — a write into the allocator's own alignment slack

## Defect
- Class: heap overflow; access: write
- Object: `a`, a 24-byte request, which any 16-byte-aligned allocator backs with 32 bytes
- In one line: writes `a[28]`, 4 bytes past the end of the **request** but still inside the **block the allocator handed out**

## How this case differs from case 0
A 24-byte request is rounded up to 32, so the 8 bytes 24..31 belong to no object: they are the allocator's slack, not a neighbour's data. `a[28]` lies in that range, so the case tests one specific boundary:

> Does the tool remember the size the program **requested**, or the block the allocator **handed out**?

- ASan records the request (24) and marks 24..31 unaddressable → reported
- LowFat's bound is the size class (32) → offset 28 is in bounds → not reported
- An annotated pool reports it only if it unpoisons exactly n bytes rather than the rounded 32. Both of ours do: `allocators/arena/arena.c` and `allocators/freelist/freelist.c` unpoison the requested n bytes, not the rounded size

## Memory layout
```
arena (16-aligned):  [ a: request 24 | slack 24..31 ][ b: 24 | slack ]
                                         ^ a[28] is here and can never reach b
```
On malloc, glibc's usable size for a 24-byte request is exactly 24 (a 32-byte chunk whose first 8 bytes hold the size), so `a[28]` is already inside the next chunk's header; ASan's right redzone reports it first.

## Expected results
See `case.json`. This is the only case in the corpus whose defect lands **only** in allocator slack, so it alone separates request-granular tools from block-granular ones.

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
