# case04-heap-overflow-read-past-pool — a read beyond the allocator's own block

## Defect
- Class: heap overflow; access: read
- Object: `a`, 24 bytes; the access is at `a + st_alloc_pool_bytes() + 8192`
- In one line: reads **outside** the whole block the CMA obtained from malloc

## The control for the other overflow rows
An overflow that stays inside the pool is invisible to malloc-granular tools; an overflow that **leaves** the pool is an ordinary overflow of the allocator's own single malloc block, and every tool regains its sight.

So a detection on this row does **not** show that the tool understands the custom allocator, only that it does not need to. The report must say so plainly, or this row of the matrix will be misread.

It is also the Tier-1 counterpart of the two real SQLite fuzz cases 29 and 31 in `corpus/real`: their images over-read by about 2 KB, past the whole 256 KiB memsys5 arena, and ASan reports the bound of the arena's global array.

## The offset is computed, not hard-coded
```c
size_t pool = st_alloc_pool_bytes();
size_t off  = pool ? pool + 8192 : 24;
st_sink(a[off]);
```
Every `st_alloc` result is at or after the pool's base, so `a + pool + 8192` is always past the end of the pool, wherever a landed. The original `+64` happened to land in a metadata block allocated right next to the pool in the Linux Valgrind development environment, a false miss; with `+8192` both ASan and Valgrind report the overflow past the pool. The distance still has to be re-checked on the real server. `st_alloc_pool_bytes()` was added to `alloc.h` for this case (A2.7); an allocator without a pool returns 0.

malloc has no pool, so the "container" is the object itself, the offset degenerates to 24 and the case degenerates to case 1 — this column must be DETECTED; it is the baseline of the row.

## Expected results
See `case.json`. LowFat does **not** report the malloc column (offset 24 is inside the size class, as in case 1) and does report the arena columns.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow |
| none | MISSED | MISSED | MISSED |

That run used the old `+64` offset; the table only records the development result of the time. The `ST NOTE` for the new offset is kept in the stdout of later runs, for re-checking.

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

This run used the `+8192` offset: under the arena and the free list stdout records `ST NOTE pool_bytes=1048576 offset=1056768`, and under malloc it degenerates to `offset=24`. The two free-list columns match the arena columns: both report the overflow past the pool.

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | DETECTED tag-mismatch | DETECTED tag-mismatch | DETECTED tag-mismatch | DETECTED tag-mismatch | DETECTED tag-mismatch |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. Every column is DETECTED: the read leaves the backing block.
