# allocators — one implementation of `corpus/include/alloc.h` per layer (Part B)

| directory | layer | what it is | annotation hooks |
|---|---|---|---|
| `malloc/` | baseline | forwards to libc malloc/free | none needed |
| `arena/` | CMA | one big malloc'd block, bump pointer, free does not reclaim storage; a side table records object sizes and liveness | ASan poison the block at init, unpoison each object on alloc, re-poison on free; Valgrind `CREATE_MEMPOOL` / `MEMPOOL_ALLOC` / `MEMPOOL_FREE` |
| `freelist/` | CMA | fixed size classes (32, 64, 128, 256), singly linked free lists carved from one backing block; free pushes, alloc pops (LIFO so UAF reuse is immediate) | as arena, plus temporary access to the in-slot free-list link |
| `sqlite/` | real CMA | SQLite `memsys5` (power-of-two buddy over a static heap) and lookaside; built from the amalgamation with `SQLITE_ENABLE_MEMSYS5` | memsys5 generated patch handles ASan poison and Valgrind mempool; lookaside `ANNOT=1` is rejected |
| `annotations/` | shared | `st_annot.h`: `ST_POISON(p,n)` / `ST_UNPOISON(p,n)` / `ST_POOL_*` that expand to ASan, Valgrind or nothing depending on `ST_ANNOT` and the tool being built for |

Each directory has a `README.md` stating the three layout facts `alloc.h` asks for, and a
`rewrite/` subdirectory for the professor's point: the same allocator rewritten to hand every
request straight to malloc, with the diff and a line count. The rewrite is a separate arm of
the matrix (`ST_ALLOC=arena-rewrite`), not a replacement.

Selected by the build with `-DST_ALLOC=<name>`; the Makefile selects the matching source.
