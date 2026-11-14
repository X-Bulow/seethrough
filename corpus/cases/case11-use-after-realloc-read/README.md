# case11-use-after-realloc-read — reading the old pointer after realloc moved the object

## Defect
- Class: use after free; access: read
- Object: `a`, 24 bytes, grown by `st_realloc(a, 4096)`; when realloc moves it, the old block is freed
- In one line: there is **no free in the source**, yet the old pointer is dead

## Why it is a separate case
`st_realloc(p, bigger)` may move the object, freeing the old block when it does. Any pointer taken before the call dangles afterwards — one of the commonest sources of UAF in real programs, and because no `free()` appears in the source, code review rarely catches it:
- SQLite's agginfo defect (capstone case 01) has exactly this shape
- so do PostgreSQL's `repalloc`-related rows

What separates it from cases 8 and 9 is that the action ending the lifetime happens **inside the allocator**, so an allocator can get it right or wrong on its own: an arena that grows in place has no such defect at all, while an allocator that copies must poison the old block when it moves.

## Precondition
`ST NOTE realloc=1 moved=1` means the call succeeded **and** the object really moved. `requires` in `case.json` watches for `moved=1`:
- the arena's and the free list's `st_realloc` both "allocate, copy, `st_free` the old block", so they always move (the arena since B1.2; before that it returned NULL and the whole column was UNSUPPORTED)
- an allocator that grows in place prints `moved=0` → the old pointer is still valid and there is no defect to report

## Trigger
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
big = st_realloc(a, 4096);     // moves; the old block is freed
st_sink(a[0]);                 // the defect
```
The control reads `big[0]`.

## Expected results
See `case.json`. LowFat's whole row is UNSUPPORTED (bounds only).

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-use-after-free | UNSUPPORTED (no realloc) | UNSUPPORTED |
| none | MISSED | UNSUPPORTED | UNSUPPORTED |

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-use-after-free | **MISSED** | **DETECTED use-after-poison** | MISSED | DETECTED use-after-poison |
| none | MISSED | **MISSED** | **MISSED** | MISSED | MISSED |

The bold cells differ from the 2026-11-05 run: before B1.2 the arena's `st_realloc` returned NULL and the whole column was UNSUPPORTED; now it always moves, so the unannotated arena is MISSED and the annotated arena DETECTED.

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. Annotated, `st_free` retags the old block that `st_realloc` left behind.

## Formal results (2026-11-13)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 | memsys5 a0 | memsys5 a1 | lookaside | arena-rewrite | freelist-rewrite |
|---|---|---|---|---|---|---|---|---|---|---|
| asan | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| valgrind | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| hwasan | DETECTED | MISSED | DETECTED | MISSED | DETECTED | — | — | — | — | — |

ASan and Valgrind: lab server, x86-64 (`results/2026-11-13-lab-core`, `-memsys5`, `-lookaside`, `-rewrite`; commit `6b54739`); every bug cell is identical to the EC2 bundles of 2026-11-10. HWASan: aarch64 Lima VM (`results/2026-11-13-lima-hwasan`, commit `c214ad3`); it was not run on the SQLite or rewrite arms. Every negative control was CLEAN. MISSED (SEGV) means the program crashed after READY inside the tool's signal handler, without a report on the defect.
