# arena

- Between two consecutive objects: nothing but alignment slack to 16 bytes (no header).
- Reuse after free: never. `st_free` ends the object's lifetime in a side table but does not
  reclaim its slot; storage comes back only at `st_alloc_fini`. With annotations off, the old
  bytes remain accessible, so a use-after-free stays hidden inside the backing block.
- Size classes: none.
- Object sizes and liveness are kept in a separate table allocated with libc `realloc`; there
  is no header between arena objects. `st_realloc` allocates a new slot, copies the preserved
  prefix, then frees the old slot. The pool-size query returns the backing block's byte count.

## Annotated arm (ST_ANNOT=1)
- ASan: whole block poisoned at init; each `st_alloc(n)` unpoisons exactly `n` bytes, leaving
  the slack poisoned; `st_free` re-poisons the object's recorded size.
- Valgrind: the backing block starts inaccessible; `VALGRIND_CREATE_MEMPOOL(base, 0, 0)` plus
  `MEMPOOL_ALLOC` / `MEMPOOL_FREE` track each object's addressability and ownership.

`st_alloc_fini` is idempotent because corpus case 12 destroys the pool before `harness/main.c`
calls it again. Adding the side table changes the annotation-feasibility result for corpus
cases 8 and 9: the annotated arena can now report a use-after-free. Older macOS smoke entries
in their `case.json` files refer to the pre-bookkeeping implementation and remain historical.

## rewrite/
`arena-rewrite.c`: the professor's point. Same interface, every `st_alloc` is a `malloc`, every
`st_free` a `free`. Diff and line count go in `rewrite/README.md`.
