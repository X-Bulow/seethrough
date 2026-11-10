# Arena rewrite

This arm replaces the pool implementation with one `malloc` per object, `free`
per release and libc `realloc`. The public `st_alloc` interface stays the same;
there is no backing pool, so `st_alloc_pool_bytes()` returns zero and
`st_alloc_fini()` does nothing. It changes allocation lifetime and reuse
semantics: bulk destruction no longer releases individual objects.

The original implementation is 101 lines; the replacement is 14 lines and
implements all seven interface functions. It removes the bump cursor, pool,
side table and annotation hooks. This is a separate matrix arm, leaving the
original allocator available for comparison.
