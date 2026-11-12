# case13-double-free — the same pointer freed twice

## Defect
- Class: double free; access: free
- Object: `a`, 24 bytes; `b` is allocated too, only so that the control has a legitimate second free
- In one line: `st_free(a)` and then `st_free(a)` again

## Trigger
```c
a = st_alloc(24);  b = st_alloc(24);
st_free(a);
ST_READY();
st_free(a);        // the defect; b is left to st_alloc_fini
```
The control frees `b` the second time. **Both images call `st_free` exactly twice** — this must hold, or a tool that reports on the third free call but not the second would be mistaken for a detector. The price is that the bug image leaks b, so Valgrind runs with `--leak-check=no`.

## Under a CMA this "defect" may not exist at all
| allocator | what the second free does |
|---|---|
| malloc | libc finds the chunk already on a free list; ASan reports `attempting double-free` |
| arena (B1.2) | `st_free` only clears the liveness flag in the side table; the second call finds the object dead and does nothing; there is no state to corrupt |
| free list | the same block is pushed onto the list twice, and the allocator is now committed to handing one address to two callers → case 15 |

The program really does violate the allocator's contract, but the arena has no state that can be corrupted, so no tool that only watches accesses can see it. This is an honest MISSED: the defect is in the program, and the arena's "tolerance" is why nobody reports it. The one exception is annotated Valgrind: the arena passes every `st_free` to `VALGRIND_MEMPOOL_FREE`, and the second time it passes a block the pool no longer holds.

## This row separates what the two annotation interfaces can express
> ASan's `POISON` / `UNPOISON` describe **addressability**; a double free is an error of **ownership**, and there is no access to instrument at all. So however it poisons, ASan's annotation interface cannot express it.
>
> Valgrind's `MEMPOOL_FREE` describes **allocation identity**: freeing a block the pool does not currently hold is reported.

So in the annotated columns ASan is MISSED, while Valgrind's arena and free-list columns are both DETECTED (before B1.2 the arena did not call `MEMPOOL_FREE`, and its column was predicted MISSED). This is the core example where the report compares the two interfaces.

## Expected results
See `case.json`.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED `attempting double-free` | MISSED | **MISSED** |
| none | MISSED | MISSED | MISSED |

The annotated arena is still MISSED, consistent with the prediction that poisoning cannot express ownership. The Valgrind column has to be measured on the server (not installed locally).

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED `attempting double-free` | MISSED | MISSED | MISSED | MISSED |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

Under ASan the annotated arena and free list are both MISSED, consistent with "poisoning cannot express ownership". The Valgrind columns have to be measured on the server (not installed locally).

## Local smoke run (2026-11-11, HWASan, Apple M5 Lima VM, Ubuntu 26.04.1 aarch64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| hwasan | DETECTED invalid-free | MISSED | MISSED | MISSED | MISSED |

HWASan cannot run on the x86-64 lab VM; this ran in the aarch64 VM described in `docs/hwasan.md`. Unannotated, every object in a pool carries the pool's tag; the a1 columns tag each object through the `ST_TAG_*` macros in `st_annot.h`. The pool columns are MISSED: `st_free` makes no tagged access, and a tag cannot report a free call.
