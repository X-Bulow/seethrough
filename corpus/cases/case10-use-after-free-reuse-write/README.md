# case10-use-after-free-reuse-write — a write through the old pointer after the storage has been handed to someone else

## Defect
- Class: use after free; access: write
- Object: `a`, 24 bytes, is freed; `b = st_alloc(24)` receives a's storage; the write through `a` lands in `b`'s data
- In one line: one address, two owners, and the write corrupts a **live** object

## The most important row in the study: the ceiling on annotation
```c
a = st_alloc(24);  st_free(a);
b = st_alloc(24);              // the free list hands a's storage straight back: b == a
printf("ST NOTE reuse=%d\n", b == a);
a[0] = 0x22;                   // the defect: a write through the stale pointer corrupts b
st_sink(b[0]);
```
At the moment of the access this memory is **legitimately live**, owned by b, and must be unpoisoned, or b's own accesses would be false positives. Therefore:

> No scheme that "colours memory" (ASan poisoning, Valgrind mempools) can tell apart two pointers to the same address. Only a mechanism that tags the **pointers** themselves can.

That is why HWASan should win this row on its own: the stale pointer still carries a's tag, while the granule now carries b's. If C3 shows that we can run HWASan, this is the cell most worth reporting.

## Precondition
The case prints `ST NOTE reuse=1` when the allocator really handed the storage back; `requires` in `case.json` records a row whose condition fails as UNSUPPORTED instead of MISSED. This took effect in the first local smoke run, and **the same case reaches different conclusions under different tools**:
- `asan + malloc`: ASan's quarantine delays reuse, `b != a` → UNSUPPORTED
- `none + malloc`: no quarantine, glibc/libmalloc reuses at once, `b == a` → the condition holds, recorded as MISSED
- any arena: never reuses → UNSUPPORTED

In other words ASan's quarantine makes this scenario **impossible to construct** on malloc, which is a finding in itself: the quarantine trades memory for a whole class of aliasing defects.

## Memory layout
```
free list, size class 32:
  st_free(a)   → list head = a
  st_alloc(24) → pops the list head = a, so b == a
  a and b are the same address; the pointer a has "expired", but the memory is live
```

## Expected results
See `case.json`. The main points: the annotated ASan and Valgrind columns are all MISSED (the ceiling), and HWASan's free-list column is DETECTED, marked to verify.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | UNSUPPORTED (quarantine, no reuse) | UNSUPPORTED (arena never reuses) | UNSUPPORTED |
| none | MISSED (reused, no tool to report it) | UNSUPPORTED | UNSUPPORTED |

At the time no allocator reused storage; the real measurement had to wait for the B1.3 free list, see the next section.

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | UNSUPPORTED (quarantine, no reuse) | UNSUPPORTED (arena never reuses) | UNSUPPORTED | MISSED | MISSED |
| none | MISSED (reused, no tool to report it) | UNSUPPORTED (arena never reuses) | UNSUPPORTED | MISSED | MISSED |

The B1.3 free list reuses immediately, so the precondition holds (`ST NOTE reuse=1`). Both ASan columns are MISSED: at the moment of the write the memory belongs to the live `b` and has to be unpoisoned. This matches the predicted ceiling.
