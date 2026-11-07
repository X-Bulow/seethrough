# case12-use-after-pool-destroy-read — a read after the whole pool's lifetime has ended

## Defect
- Class: use after free; access: read
- Object: `a`, 24 bytes, **never freed individually**; `st_alloc_fini()` frees the whole pool it lives in
- In one line: the object was not freed, its container was, and the pointer survived

## The only defect that exists because there is a CMA
This is PostgreSQL's `MemoryContextReset`, Apache's `apr_pool_destroy`, and every arena's "free everything at once when the request ends". The very usage that makes arenas attractive is the one that creates this bug. And there is no per-object bookkeeping involved at all — there never was.

## The result is a neat asymmetry
> An arena **hides** accesses that happen inside its pool and **exposes** accesses that happen after it.

Because the pool is itself one malloc block, malloc-granular tools can see its lifetime. So this row is reported without any annotation, and the annotated columns do no better. It is the mirror image of case 8: case 8 is the hardest row under an arena, case 12 the easiest, and both are the same class of defect.

## Precondition
`ST NOTE pool=1` means the allocator really has a pool. Under malloc `st_alloc_fini` is a no-op, the object stays alive and the read is **legal** — the first local smoke run exposed this at once (the original prediction was DETECTED, the result MISSED, because nothing happened). Hence the `requires`: the malloc column is UNSUPPORTED by construction, and its equivalent is case 9.

`st_alloc_fini()` is called once by this case and again afterwards by `harness/main.c`, so `alloc.h` requires every allocator's `st_alloc_fini` to be **idempotent** (both pool allocators start it with `if (!base) return;`).

## Trigger
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
printf("ST NOTE pool=%d\n", st_alloc_pool_bytes() > 0);
st_alloc_fini();               // the pool's lifetime ends; a was never freed
st_sink(a[0]);                 // the defect
```
The control moves the read before `st_alloc_fini()`.

## Expected results
See `case.json`: asan and valgrind are DETECTED in every arena and free-list column, and the malloc column is UNSUPPORTED.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | UNSUPPORTED (no pool) | DETECTED heap-use-after-free | DETECTED heap-use-after-free |
| none | UNSUPPORTED | MISSED | MISSED |

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | UNSUPPORTED (no pool) | DETECTED heap-use-after-free | DETECTED heap-use-after-free | DETECTED heap-use-after-free | DETECTED heap-use-after-free |
| none | UNSUPPORTED | MISSED | MISSED | MISSED | MISSED |

The two free-list columns agree with the two arena columns.
