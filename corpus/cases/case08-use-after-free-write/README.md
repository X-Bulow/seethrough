# case08-use-after-free-write — a write after free, with no allocation in between

## Defect
- Class: use after free; access: write
- Object: `a`, 24 bytes, freed and then written
- In one line: `a[0] = 1` after `st_free(a)`

## Trigger
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
st_free(a);
ST_READY();
a[0] = 1;              // the defect
```
Control: the same single allocation and single free, with the write **moved before the free**. The two images have byte-identical allocation traffic; they differ only in the order of the access and the free.

## This row measures whether annotation can do it, not whether the tool supports it
Nothing is allocated in between, so the only fact a tool can go on is that the lifetime ended. That is precisely what a CMA does not record:

| allocator | what happens on free | can the annotated column win it back |
|---|---|---|
| malloc | the block enters the quarantine and ASan paints its shadow "freed" | — |
| pure bump arena (before B1.2) | `st_free` is a no-op; the bytes are as live as before the free | **no**: `st_free` does not know the object's size, so it cannot re-poison precisely |
| arena + side table (B1.2) | the side table records each object's size and liveness, and `st_free` re-poisons by size | **yes**, at the cost of per-object bookkeeping in the allocator |
| free list | the block goes onto its size-class list | yes: it knows the size class and can poison the whole block |

So whether annotation works depends on the **allocator's design**, not on tool support: a pure bump arena does not record object sizes and annotation cannot win this back; only after B1.2 gave the arena a side table outside the pool could it. The cost of annotation is not only a few macros but per-object bookkeeping the allocator did not otherwise need. This is the main example for the report's "annotation feasibility" section, and part of what B2.3 records (see `docs/allocator-annotations.md`).

## Expected results
See `case.json`. LowFat's whole row is UNSUPPORTED: it checks bounds only and has no notion of a lifetime.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | **MISSED** |
| none | MISSED | MISSED | MISSED |

At the time the annotated arena still missed, as predicted; this README had already said to re-run after B1.2 and keep both results, see the next section.

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | **DETECTED use-after-poison** | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

The bold cell differs from the 2026-11-05 run. Once B1.2 gave the arena a side table, the annotated arena re-poisons by size on free and becomes DETECTED. Both results are kept in `measured` in `case.json`, and that difference answers "what does annotation cost": not only a few macros, but per-object bookkeeping.

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. Annotated, `st_free` hands the object back to the pool's tag, so the stale pointer mismatches.

## Formal results (2026-11-13)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 | memsys5 a0 | memsys5 a1 | lookaside | arena-rewrite | freelist-rewrite |
|---|---|---|---|---|---|---|---|---|---|---|
| asan | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| valgrind | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | DETECTED | DETECTED |
| hwasan | DETECTED | MISSED | DETECTED | MISSED | DETECTED | — | — | — | — | — |

ASan and Valgrind: lab server, x86-64 (`results/2026-11-13-lab-core`, `-memsys5`, `-lookaside`, `-rewrite`; commit `6b54739`); every bug cell is identical to the EC2 bundles of 2026-11-10. HWASan: aarch64 Lima VM (`results/2026-11-13-lima-hwasan`, commit `c214ad3`); it was not run on the SQLite or rewrite arms. Every negative control was CLEAN. MISSED (SEGV) means the program crashed after READY inside the tool's signal handler, without a report on the defect.
