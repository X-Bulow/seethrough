# freelist

- Between two consecutive fresh objects: only the unused tail of the previous slot. There is
  no in-band header. Different requests can have different classes, so slot sizes may differ.
- Reuse after free: immediate, LIFO within the same size class. The next link is stored in the
  first pointer-sized word of a freed slot. An unreported UAF write can corrupt that link.
- Size classes: 32, 64, 128, 256 bytes. A 24-byte request occupies a 32-byte slot, with 8
  bytes of slack. Requests above 256 bytes get a 16-byte-aligned slot from the same backing
  block but are not recycled. `st_realloc` allocates a new slot, copies the preserved prefix,
  then frees the old one.
- A separate table records each slot's requested size, class and liveness for `realloc` and
  annotation. Both the table and the backing block are released by the idempotent `st_alloc_fini`.

## Annotated arm (`ST_ANNOT=1`)

- ASan poisons the whole backing block at initialization, unpoisons exactly the requested
  bytes on allocation, and poisons the full slot on free. The link word is briefly made
  accessible only while the allocator reads or writes it.
- Valgrind creates one mempool, starts the backing block inaccessible, and uses
  `MEMPOOL_ALLOC` / `MEMPOOL_FREE` for object identity. The link word is temporarily marked
  defined while the allocator handles it, then made inaccessible again.
- Both tools can see accesses to a freed slot before reuse. Once the slot is reissued to a
  new live object, the same address must be accessible, so neither ASan's shadow nor
  Memcheck's addressability alone distinguishes a stale pointer from the new owner.
- ASan's poisoning interface does not express ownership: double free and freeing an
  interior pointer can remain silent. Valgrind's mempool requests can report those frees.

The annotation boundaries and limitations are detailed in
[docs/allocator-annotations.md](../../docs/allocator-annotations.md).
