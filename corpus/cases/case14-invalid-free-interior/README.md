# case14-invalid-free-interior — freeing a pointer into the middle of an object

## Defect
- Class: invalid free; access: free
- Object: `a`, 24 bytes; the case executes `st_free(a + 8)`
- In one line: the pointer passed to free is not the one `st_alloc` returned

## How real programs get here
Freeing a struct member, freeing a pointer that was advanced during parsing, or freeing the payload of an object whose header belongs to the allocator.

## The one class where the malloc baseline is enforced by the allocator itself
glibc and ASan both reject it outright: the chunk header is not where they expect it. So the malloc column of this row is reported not by the tool's instrumentation but by the allocator's own check.

| allocator | consequence of `st_free(a + 8)` |
|---|---|
| malloc | rejected immediately (ASan: `attempting free on address which was not malloc()-ed`) |
| arena (B1.2) | finds no `a+8` in its side table and does nothing; when annotated it passes `a+8` to `VALGRIND_MEMPOOL_FREE` |
| free list | pushes `a+8` onto a size-class list and later hands it out, so every later object in that class is misaligned by 8 bytes against the block it occupies — the damage is real, but it appears far away |

Because the free list's damage appears so far away, this case records only what the free did and does not rely on a later crash as proof.

## Trigger
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
ST_READY();
st_free(a + 8);    // the defect
```
The control frees `a`. Each image makes one allocation and one free.

## Expected results
See `case.json`. ASan's annotated free-list column was marked DETECTED, to verify; the local run of 2026-11-07 measured MISSED: the free list unpoisons those 8 bytes before writing its link word, so ASan sees no bad access, for the same reason as case 13. Valgrind's two annotated columns are predicted DETECTED: `VALGRIND_MEMPOOL_FREE` given an address that is not a pool allocation reports an invalid free.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED `attempting free on address which was not malloc()-ed` | MISSED | MISSED |
| none | MISSED | MISSED | MISSED |

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED `attempting free on address which was not malloc()-ed` | MISSED | MISSED | MISSED | MISSED |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

The annotated free list is MISSED; the earlier DETECTED, marked to verify, was wrong: the free list unpoisons those 8 bytes before writing its link word, so ASan sees no bad access.

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | MISSED | MISSED | MISSED | MISSED | MISSED |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. MISSED on malloc as well: HWASan's free accepted the interior pointer without a report.

## Formal results (2026-11-13)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 | memsys5 a0 | memsys5 a1 | lookaside | arena-rewrite | freelist-rewrite |
|---|---|---|---|---|---|---|---|---|---|---|
| asan | DETECTED | MISSED | MISSED | MISSED | MISSED | MISSED | MISSED | MISSED | DETECTED | DETECTED |
| valgrind | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| hwasan | MISSED | MISSED | MISSED | MISSED | MISSED | — | — | — | — | — |

ASan and Valgrind: lab server, x86-64 (`results/2026-11-13-lab-core`, `-memsys5`, `-lookaside`, `-rewrite`; commit `6b54739`); every bug cell is identical to the EC2 bundles of 2026-11-10. HWASan: aarch64 Lima VM (`results/2026-11-13-lima-hwasan`, commit `c214ad3`); it was not run on the SQLite or rewrite arms. Every negative control was CLEAN. MISSED (SEGV) means the program crashed after READY inside the tool's signal handler, without a report on the defect.
