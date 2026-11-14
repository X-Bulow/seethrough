# case15-double-free-after-reuse — freeing again after reuse, pulling a live object's block out from under it

## Defect
- Class: double free; access: free
- Object: `a`, 24 bytes, is freed; `b = st_alloc(24)` receives a's storage; `st_free(a)` actually frees b's block
- In one line: the second free looks perfectly legal; what gets corrupted is "who owns this memory"

## Why double free is split into two cases
```c
a = st_alloc(24);  st_free(a);
b = st_alloc(24);              // the free list serves it from a's storage: b == a
printf("ST NOTE reuse=%d\n", b == a);
st_free(a);                    // the defect: frees an address the allocator considers live and owned by b
st_sink(b[0]);                 // b is now a freed block
```
On a free list that reuses immediately, `a == b`, so the second free is **indistinguishable** from correctly freeing b: no tool can object to it. The defect only shows when b is used afterwards — the read at the end of this case.

So detection on this row **comes from the read, not from the free**, and the report must say so. Compare case 13: there the storage is not reused (malloc has a quarantine), so the second free is itself a double free.

## Contrast with case 10: this time annotation wins
In case 10 the memory is live at the moment of the access, and annotation can do nothing. Here it is different: in the annotated implementation the defective free **poisons b's storage**, and the read right after it is an access to poisoned memory → reported.

> In the same "one address, two owners" situation, whether annotation can win it back depends on whether the faulty operation is an **access** or a **free**: a free leaves a trace that can be painted, an access does not.

## Precondition
`ST NOTE reuse=1`; without reuse this is case 13. ASan's quarantine and the arena's lack of reuse make those columns UNSUPPORTED by construction (see case 10).

## Expected results
See `case.json`: the unannotated free-list column is MISSED, the annotated one DETECTED (via the read).

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | UNSUPPORTED (quarantine, no reuse) | UNSUPPORTED (arena never reuses) | UNSUPPORTED |
| none | MISSED (reused, no tool to report it) | UNSUPPORTED | UNSUPPORTED |

At the time no allocator reused storage; the real measurement had to wait for the B1.3 free list, see the next section.

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | UNSUPPORTED (quarantine, no reuse) | UNSUPPORTED (arena never reuses) | UNSUPPORTED | MISSED | DETECTED use-after-poison |
| none | MISSED (reused, no tool to report it) | UNSUPPORTED (arena never reuses) | UNSUPPORTED | MISSED | MISSED |

The free-list precondition holds. Unannotated it is MISSED; annotated, the stale free poisons `b`'s storage and the following read is reported as use-after-poison, so DETECTED. This matches the prediction: the detection comes from the read, not from the free.

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | DETECTED invalid-free | UNSUPPORTED (arena never reuses) | UNSUPPORTED (arena never reuses) | MISSED | DETECTED tag-mismatch |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. malloc reports invalid-free at the stale `st_free`; the annotated free list reports `b`'s read after its slot went back to the pool's tag.

## Formal results (2026-11-13)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 | memsys5 a0 | memsys5 a1 | lookaside | arena-rewrite | freelist-rewrite |
|---|---|---|---|---|---|---|---|---|---|---|
| asan | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | UNSUPPORTED | UNSUPPORTED |
| valgrind | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | MISSED | DETECTED | MISSED | DETECTED | MISSED | UNSUPPORTED | UNSUPPORTED |
| hwasan | DETECTED | UNSUPPORTED | UNSUPPORTED | MISSED | DETECTED | — | — | — | — | — |

ASan and Valgrind: lab server, x86-64 (`results/2026-11-13-lab-core`, `-memsys5`, `-lookaside`, `-rewrite`; commit `6b54739`); every bug cell is identical to the EC2 bundles of 2026-11-10. HWASan: aarch64 Lima VM (`results/2026-11-13-lima-hwasan`, commit `c214ad3`); it was not run on the SQLite or rewrite arms. Every negative control was CLEAN. MISSED (SEGV) means the program crashed after READY inside the tool's signal handler, without a report on the defect.
