# case01-heap-overflow-read — a one-byte read past the end

## Defect
- Class: heap overflow; access: read
- Object: `a`, 24 bytes, the first of two consecutive `st_alloc(24)` calls
- In one line: reads `a[24]`, one byte past the end of the request

## Trigger
The same allocation sequence as case 0; the defect line is `st_sink(a[24])`, and the control reads `a[23]`.

## Why a read gets its own case
Rule 4 in `corpus/README.md`: reads and writes are separate cases. The reason is not formalism:
- an out-of-bounds **read** corrupts nothing, so nothing will ever crash because of it later; there is no "late evidence"
- Valgrind reports an invalid read only when the byte is **unaddressable**, and inside an arena every byte is addressable
- ASan instruments reads and writes separately, so one can be caught while the other is missed

Under an arena the read also quietly returns whatever byte sits in a's slack, so the program cannot notice either.

## Memory layout
As case 0: `a[24]` lands inside a's 16-byte alignment slack (24..31), not in b's data.

## Expected results
As case 0 (see `case.json`). LowFat does not report even on malloc, because 24 is inside the 32-byte size class.

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
