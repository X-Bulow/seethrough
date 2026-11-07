# case06-heap-underflow-read — a one-byte read before the start

## Defect
- Class: heap underflow; access: read
- Object: `a`, 24 bytes, allocated after another 24-byte object `first`
- In one line: reads `*(a - 1)`

## Trigger
The same allocation sequence as case 5, with the defect line `st_sink(*(a - 1))`; the control reads `a[0]`.

Why a read gets its own case: see case 1. Why the two sides of an object are not symmetric: see case 5.

## Memory layout
As case 5: `*(a-1)` is the last alignment-slack byte of `first`.

## Expected results
As case 5 (see `case.json`).

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED |

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

The two free-list columns agree with the two arena columns.
