# case07-heap-underflow-write-metadata — overwriting the 8 bytes where a header would be

## Defect
- Class: heap underflow; access: write
- Object: `a`, 24 bytes; the write covers `a-8 .. a-1`
- In one line: overwrites the 8 bytes in which an allocator keeps the "size"

## The ground-truth version of capstone's memsys5 demonstrator
An allocator that keeps its bookkeeping **next to or inside** user blocks (in-band) turns a small overflow into corruption of the allocator itself:
- glibc keeps the chunk size at `p - 8`
- memsys5 writes its free-list links **inside the body of freed blocks** (`capstone/bug-corpora/sqlite/engine-repros/18_mem5-design_*`)

So the same source line means something different under each allocator, which is exactly what is measured:
| allocator | what `a-8 .. a-1` is | consequence |
|---|---|---|
| malloc | the chunk header (size) | ASan's left redzone reports it first; without a tool `free()` may abort |
| bump arena | no header, just `first`'s slack | nobody notices |
| free list (B1.3) | also just `first`'s slack: the bookkeeping is in a side table outside the pool, and link words are written only into freed slots | unannotated, nobody notices; annotated, the range is poisoned and the write is detected |

The `none` column (no tool at all) is especially informative here: it records whether the program later crashed inside the allocator.

## Memory layout
```
arena:   [ first: 24 | slack 24..31 ][ a: 24 | slack ]
                         ^^^^^^^^ these 8 bytes are a-8..a-1
glibc:   [ prev_size | size (8B) ][ a: 24 ...
                       ^^^^^^^^ a-8..a-1
```

## Expected results
See `case.json`. The annotated free-list columns were marked to verify, pending whether B's implementation had an in-band header. The B1.3 free list has none: `a-8..a-1` is `first`'s slack, poisoned when annotated, and the local ASan smoke run confirms DETECTED. Neither of our pool allocators keeps an in-band header, so in this case glibc's header is the only allocator state that can be corrupted.

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

The annotated free-list column is confirmed DETECTED (it was marked to verify): the B1.3 free list has no in-band header, `a-8..a-1` is `first`'s slack, and it stays poisoned when annotated.

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch | MISSED | DETECTED tag-mismatch |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. Annotated, `first` and `a` carry different tags.
