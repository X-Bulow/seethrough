# case09-use-after-free-read — a read after free, with no allocation in between

## Defect
- Class: use after free; access: read
- Object: `a`, 24 bytes, freed and then read
- In one line: `st_sink(a[0])` after `st_free(a)`

## Trigger
The same as case 8 with a read instead of the write; the control moves the read before the free.

## Why it is the quietest class of defect
A stale read corrupts nothing, so no later crash will point back at it. In the unannotated arena `st_free` reclaims nothing, so the read returns the object's own old contents (0x5a), and neither the program nor a tool that only watches malloc lifetimes can notice.

In the real world this class is the large majority: in capstone's SQLite engine corpus, 19 of the 27 counted cases are temporal, most of them stale reads (see `corpus/real/README.md`).

## Expected results
As case 8 (see `case.json`): since B1.2 the arena records object sizes in a side table, so the annotated arena re-poisons on free and detects the read; the unannotated arena and free list still miss.

## Local smoke run (2026-11-05, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | MISSED |
| none | MISSED | MISSED | MISSED |

## Local smoke run (2026-11-07, after merging B1.2/B1.3, macOS arm64, development only, not citable)
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | **DETECTED use-after-poison** | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

The bold cell differs from the 2026-11-05 run, for the same reason as case 8.
