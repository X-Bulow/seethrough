# A5.13: review of every MISSED verdict

Date 2026-11-14, by A. Question: is any MISSED (or FALSE-POSITIVE) in the formal results caused
by the build, by optimisation or by the harness, rather than by the tool and the allocator?
Answer: no. Every miss below was executed, silent and reproducible, and each one has a
mechanism that the case was built to expose.

Bundles: `results/2026-11-13-lab-{core,memsys5,lookaside,rewrite}` (ASan, Valgrind; 352 bug
rows) and `results/2026-11-13-lima-hwasan` (HWASan; 96 bug rows). Re-run the checks with

    python3 harness/audit-missed.py results/2026-11-13-lab-* \
        --replica results/2026-11-10-ec2-b-{core,memsys5,lookaside,rewrite} --list
    python3 harness/audit-missed.py results/2026-11-13-lima-hwasan --list

## Mechanical checks (all passed)

| check | how | result |
|---|---|---|
| detection builds are `-O0 -g` | `Makefile` `OPT ?= -O0 -g`; `run-matrix.py` never passes `OPT` | the compiler cannot delete or move the defective access |
| tree was clean | `env.txt` of every bundle | `dirty=0` in all five |
| no false reports | negative controls, same allocation traffic, one line changed | 448/448 CLEAN; 0 FALSE-POSITIVE, 0 TOOL-ERROR |
| the defect line ran | `ST READY` printed immediately before the access | in all 174 MISSED rows |
| the program then finished | `ST DONE` and exit 0, or a recorded crash after READY | 170 finished; 4 crashed in ASan's signal handler (case 4) |
| the tool really said nothing | stderr searched for any ASan/HWASan report type, Valgrind `Invalid read/write/free`, `Mismatched free`, uninitialised use, UBSan and LowFat messages | none, apart from the `SEGV on unknown address` of the 4 crashes |
| Memcheck agreed | `ERROR SUMMARY: 0 errors` | in all 59 Valgrind MISSED rows |
| the access is instrumented | the same case on malloc, same flags | DETECTED for 140 of the 174 misses; the rest are cases 10 and 15 (UNSUPPORTED on malloc: no immediate reuse under ASan's quarantine or Memcheck's allocator), case 3 under ASan, case 14 under HWASan, and the HWASan case 4 cell, all explained below |
| it is not a property of one machine | lab server vs the EC2 bundles (2763402) | 352/352 bug cells identical |
| HWASan formal vs development run | `case.json` 2026-11-11 Lima entry | 95/96 identical; the difference is C7 |
| MISSED where `case.json` predicted DETECTED | after the A2.9 corrections | only C7 |

## Why each miss happens

| | mechanism | cells | cases | tools |
|---|---|---:|---|---|
| C1 | the pool hides the object: unannotated Arena, Free list, memsys5, lookaside; the access stays inside the one block the tool knows | 122 | 0-2, 5-11, 13-15 | ASan 50, Valgrind 50, HWASan 22 |
| C2 | the overflow lands in another live object, which is addressable whatever the annotation | 20 | 3 | ASan 11 (every arm, malloc and rewrite included: offset 64 clears ASan's redzone), Valgrind 7 (pools; malloc is DETECTED because Memcheck's own allocator spaces blocks apart), HWASan 2 (unannotated pools; annotated pools tag the neighbour differently and detect) |
| C3 | a stale pointer to storage already reissued to a new owner; address-based annotation cannot tell the two pointers apart | 4 | 10 | ASan, Valgrind on annotated Free list and memsys5 (HWASan's annotated Free list gives a new tag and detects) |
| C4 | a bad `free` that touches no byte: poisoning and tagging describe access, not ownership | 14 | 13, 14 | ASan 6 (annotated pools; Valgrind's mempool requests do express it), HWASan 8 (annotated pools, and case 14 on every arm) |
| C5 | HWASan's tag interface is 16-byte precise, so a 1-byte overflow into the rounding slack keeps the object's tag | 6 | 0-2 | HWASan, annotated pools (ASan unpoisons exactly `n` bytes and detects) |
| C6 | 8192 bytes past a 1 MiB pool is outside ASan's large-allocation mapping and outside anything it poisoned: silent, or a SEGV in its signal handler | 7 | 4 | ASan, every pool arm (Valgrind sees all of them) |
| C7 | HWASan tag collision: the random pointer tag equalled the short-granule value | 1 | 4 | HWASan malloc; 198 of 200 reruns detect (`docs/hwasan.md`) |

The 67 misses in arms without a `case.json` prediction (memsys5, lookaside, the rewrites) fall
into the same classes: C1 for unannotated memsys5 and lookaside, C2/C3/C4/C6 for annotated
memsys5 exactly as for the annotated Free list, and C2 for the single ASan miss of each rewrite.

What this review does not cover: UBSan and LowFat (not run through the matrix) and the
real-SQLite corpus (`corpus/real/`, development runs only).
