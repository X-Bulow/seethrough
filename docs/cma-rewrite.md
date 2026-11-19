# Allocator rewrite configurations

`arena-rewrite` and `freelist-rewrite` implement the same seven-function `st_alloc` interface as the pooled allocators, using one libc allocation per object. Select them with `ALLOC=arena-rewrite` or `ALLOC=freelist-rewrite`. They use `ANNOT=0`: individual libc allocations already expose object boundaries to the detectors.

| Property | Pooled allocator | Rewrite |
|---|---|---|
| Object storage | Suballocation within one backing block | Individual malloc allocation |
| Reuse | Arena does not reuse; freelist immediately reuses matching slots | Depends on libc and detector quarantine |
| Free | Ends logical lifetime within the pool | Calls libc free |
| Finalization | Releases the backing pool | No pool to release; individually live allocations remain live |
| Reallocation | Allocates, copies, and ends the old lifetime | libc realloc may move or grow in place |

`st_alloc_pool_bytes()` returns zero for rewrites, and `st_alloc_fini()` does nothing. Cases that require pool destruction or immediate reuse can therefore be UNSUPPORTED. The harness checks their precondition markers rather than counting a missing precondition as successful detection.

For real SQLite defects, the `rewrite` engine configuration disables memsys5, lookaside, and the page-cache bulk pool without patching SQLite source. See [corpus/real/README.md](../corpus/real/README.md) for build flags and gating.

Rewriting changes allocation layout, lifetime, reuse, and performance. Annotation comparisons retain the allocator algorithm and vary tool requests; rewrite comparisons measure a separate implementation tradeoff. See [allocator-annotations.md](allocator-annotations.md) for annotation behavior.
