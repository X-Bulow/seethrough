# Case index

Dense numbering; `ST_CASE(n)` in each `case.c` must match `case` in its `case.json`, and
`harness/main.c` is built with `-DST_CASE_N=<n>`. Numbers 1-6 were reassigned on 2026-11-05 when
the corpus grew from 7 placeholders to these 16 cases; nothing outside this directory had cited
them yet.

Four classes, each with its read and write form, plus the variants that isolate one property of
the allocator rather than one bug class. 16 bug programs and 16 negative controls.

| n | directory | class | access | what it isolates |
|---|---|---|---|---|
| 0 | heap-overflow-write | heap overflow | write | 1 byte past the end, into the alignment slack |
| 1 | heap-overflow-read | heap overflow | read | the same access as a read |
| 2 | heap-overflow-write-slack | heap overflow | write | request bounds vs block bounds (offset 28 of 24) |
| 3 | heap-overflow-write-far | heap overflow | write | 40 past the end, into a live third object: where annotation fails |
| 4 | heap-overflow-read-past-pool | heap overflow | read | leaving the pool: every tool sees it again |
| 5 | heap-underflow-write | heap underflow | write | 1 byte before the start |
| 6 | heap-underflow-read | heap underflow | read | the same access as a read |
| 7 | heap-underflow-write-metadata | heap underflow | write | the 8 bytes an allocator keeps a header in |
| 8 | use-after-free-write | use after free | write | lifetime end with no reuse; can the allocator poison on free at all |
| 9 | use-after-free-read | use after free | read | the same access as a read |
| 10 | use-after-free-reuse-write | use after free | write | two pointers to one live address: the ceiling on annotation |
| 11 | use-after-realloc-read | use after free | read | the free hidden inside realloc |
| 12 | use-after-pool-destroy-read | use after free | read | the pool's lifetime, not the object's |
| 13 | double-free | double free | free | ownership, which poisoning cannot express |
| 14 | invalid-free-interior | invalid free | free | a pointer the allocator never handed out |
| 15 | double-free-after-reuse | double free | free | freeing a live object's storage under it |

## Preconditions

Cases 10, 11, 12 and 15 need a property of the allocator (reuse on free, a realloc that moves, a
pool to destroy). Each prints a marker and declares it in `case.json` `requires`;
`harness/run-matrix.py` records a row whose marker is missing as UNSUPPORTED, never as MISSED.
ASan's quarantine stops malloc from reusing a freed block, and a bump arena never reuses, so in
cases 10 and 15 those columns are UNSUPPORTED by construction and the comparison is between the
free list and its annotated arm. Since B1.2 the arena's realloc always moves, so case 11 is
measurable on every allocator. malloc has no pool, so case 12's malloc column is UNSUPPORTED.

## Reading the expected verdicts

`case.json` `expected` has one row per tool with a column per allocator arm
(`malloc`, `arena`, `arena+annot`, `freelist`, `freelist+annot`) and a `why`. Five rows carry the
study's main claims:

- **case 3** — annotation cannot catch a spatial overflow that lands in another LIVE object.
- **case 8** — annotation needs the allocator's cooperation: to re-poison on free, `st_free` must
  know the object's size. A pure bump arena does not, and its annotated arm missed (2026-11-05
  smoke); once B1.2 added a side table of sizes, the same arm detects it (2026-11-07). What
  annotation costs is per-object bookkeeping, not only the macros.
- **case 10** — no memory-poisoning scheme can separate two pointers to one live address; only a
  pointer-tagging mechanism (HWASan) can.
- **case 12** — an arena hides accesses inside its pool and exposes accesses after it.
- **case 13** — ASan's poison interface describes addressability, Valgrind's mempool interface
  describes ownership, and only the second can express a double free or an invalid free
  (case 14: the annotated free list is MISSED under ASan).
