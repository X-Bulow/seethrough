# arena

- Between two consecutive objects: nothing but alignment slack to 16 bytes (no header).
- Reuse after free: never; `st_free` is a no-op, memory comes back only at `st_alloc_fini`.
  So a use-after-free here is "use of memory the program said it was done with" with the data
  still intact: the classic case ASan cannot see without annotation.
- Size classes: none.

## Annotated arm (ST_ANNOT=1)
- ASan: whole block poisoned at init; each `st_alloc(n)` unpoisons exactly `n` bytes, leaving
  the slack poisoned; `st_free` re-poisons the object (needs the size -- see TODO in arena.c).
- Valgrind: `VALGRIND_CREATE_MEMPOOL(base, 0, 0)` plus `MEMPOOL_ALLOC` / `MEMPOOL_FREE`.

## rewrite/
`arena-rewrite.c`: the professor's point. Same interface, every `st_alloc` is a `malloc`, every
`st_free` a `free`. Diff and line count go in `rewrite/README.md`.
