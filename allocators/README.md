# Allocators

Interchangeable implementations of [alloc.h](../corpus/include/alloc.h), used to compare pooled allocation with malloc and tool annotations.

| Directory | Implementation |
|---|---|
| [malloc](malloc/malloc.c) | libc baseline |
| [arena](arena/arena.c) | Bump allocation with bulk cleanup |
| [freelist](freelist/freelist.c) | Size-class pools with immediate reuse |
| [arena rewrite](arena/rewrite/arena-rewrite.c) | Individual malloc allocations replacing the arena |
| [freelist rewrite](freelist/rewrite/freelist-rewrite.c) | Individual malloc allocations replacing class pools |
| [sqlite](sqlite/README.md) | SQLite memsys5 and lookaside adapters |
| [annotations](annotations/st_annot.h) | Shared detector hooks |

Select `ALLOC=<name>` and `ANNOT=0` or `1` when building. Arena and freelist also provide rewrite variants using individual malloc allocations.
