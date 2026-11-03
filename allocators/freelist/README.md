# freelist

- Between two consecutive objects: the next slot of the same size class (no header; the
  free-list link lives inside freed slots, so a UAF write can corrupt the allocator).
- Reuse after free: immediate, LIFO.
- Size classes: 32, 64, 128, 256 bytes; a 24-byte request gets 32, so an overflow of up to 8
  bytes stays inside the slot (this is the "slack" axis of stretch goal (a)).

Annotated arm and rewrite/ as in arena/README.md.
