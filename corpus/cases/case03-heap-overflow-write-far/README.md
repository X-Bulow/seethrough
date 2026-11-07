# case03-heap-overflow-write-far — a write 40 bytes past the end, over the neighbour into a live third object

## Defect
- Class: heap overflow; access: write
- Object: `a`, 24 bytes, the first of three consecutive `st_alloc(24)` calls
- In one line: writes `a[64]`. In a 16-byte-aligned arena a=[0,32) b=[32,64) c=[64,96), so `a[64]` is `c[0]`

## One of the most important rows in the corpus
It shows that **annotation has a ceiling for spatial defects too**:

> `a[64]` lands on `c[0]`. c is a live object and must be unpoisoned, or c's own accesses would be false positives. So no scheme that "poisons the gaps at allocation time" can catch this row.

Compare case 0: there the overflow lands in a's own alignment slack, and annotation wins it back. The two cases differ only in the offset, yet reach opposite conclusions. The report should present cases 0, 2 and 3 as a distance series (the full distance sweep is A6.2).

On malloc this row also tests the **width** of the redzone: if offset 64 crosses a's right redzone into b's data, ASan does not see it either.

## Memory layout
```
arena:   [ a: 24 |slack][ b: 24 |slack][ c: 24 |slack]
         0      24   32  32     56  64  64          96
                              a[64] ────────────────┘ = c[0], a live byte

malloc + ASan:  [rz][ a: 24 ][rz ≥16][rz][ b ]...
                a[64] may cross a's right redzone into b's data → not reported
```

## Expected results
See `case.json`. LowFat **does** report this row (on malloc offset 64 is beyond the 32-byte size class), the opposite of cases 1 and 2; that contrast is the core of the LowFat section.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | **MISSED** | MISSED | **MISSED** |
| none | MISSED | MISSED | MISSED |

The ASan miss on malloc has been reproduced locally (the prediction was marked to verify); the server run must confirm that Linux's ASan redzone width is the same. The miss on the annotated arena is by design, not a bug.

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | MISSED | MISSED | MISSED | MISSED | MISSED |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

The two free-list columns agree with the two arena columns.
