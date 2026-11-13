# Free-list rewrite

This arm replaces class slots and LIFO reuse with individual libc allocations.
`st_alloc_pool_bytes()` returns zero and `st_alloc_fini()` does nothing. This
removes the allocator's class slack and its deterministic immediate reuse.

The original implementation is 164 lines; the replacement is 14 lines and
implements all seven interface functions. It removes the size classes,
in-slot free links, pool, side table and annotation hooks.
