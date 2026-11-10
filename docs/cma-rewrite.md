# Part B: rewrite versus boundary annotations

## What was rewritten

`arena-rewrite` and `freelist-rewrite` implement the same seven-function
`st_alloc` interface using one libc allocation per object. Each replacement
is 14 lines, versus 101 lines for the Arena and 164 for the Free list. The
source for the two CMA implementations remains in the matrix. The rewrite
arms use `ANNOT=0`; libc already exposes the object boundary to ASan and
Memcheck.

The rewrite is small at the interface, but it changes behavior:

| Property | Pool allocator | Rewrite |
|---|---|---|
| Object boundary | Inside one backing allocation | Each object is its own libc allocation |
| Free-list reuse | Immediate LIFO reuse for a matching class | Determined by libc and sanitizer quarantine |
| Arena `st_free` | Ends logical lifetime; pool bytes are not reclaimed | Reclaims the object immediately |
| `st_alloc_fini` | Releases the entire pool | No pool exists; only objects individually freed are released |
| `st_realloc` | Always moves in these implementations | libc may grow in place or move |

Thus case 10 (stale pointer after immediate reuse) and case 12 (stale pointer
after pool destruction) can become **UNSUPPORTED** under rewrite because the
required event no longer happens. This is a semantic change, not a detector
success. The harness gates those cases with `ST NOTE reuse=1` and `pool=1`.

## Detection comparison

The final x86-64 EC2 detection bundles are listed in
[results/README.md](../results/README.md). Every negative control was
CLEAN. Formal bug verdicts for the key comparison are:

| Tool | Arm | DETECTED | MISSED | UNSUPPORTED |
|---|---|---:|---:|---:|
| ASan | Arena, unannotated | 1 | 13 | 2 |
| ASan | Arena, annotated | 10 | 4 | 2 |
| ASan | Free list, unannotated | 1 | 15 | 0 |
| ASan | Free list, annotated | 11 | 5 | 0 |
| ASan | either rewrite | 12 | 1 | 3 |
| Valgrind | Arena, unannotated | 2 | 12 | 2 |
| Valgrind | Arena, annotated | 13 | 1 | 2 |
| Valgrind | Free list, unannotated | 2 | 14 | 0 |
| Valgrind | Free list, annotated | 14 | 2 | 0 |
| Valgrind | either rewrite | 13 | 0 | 3 |

On EC2 ASan case 4 produced a signal-handler SEGV without a boundary
diagnosis for Arena and Free list, both with and without annotation. The
annotated memsys5 arm also missed it but did not signal. The development
ASan host had detected this outer-pool read. This explains the one-count
difference below; the formal EC2 table takes precedence.

In the 2026-11-10 macOS arm64 ASan development run, both SQLite CMA layers
missed the 24-byte overflow and a UAF before pool destruction; the two
rewrite arms detected them. The full 16-case bundle is
`results/scratch-b3b4-full-asan/`: each unannotated SQLite layer has 1
DETECTED and 15 MISSED bug rows; each rewrite has 12 DETECTED, 1 MISSED and
3 UNSUPPORTED. All 64 negative controls are CLEAN. Under Valgrind, each
unannotated SQLite layer had 2 DETECTED and 14 MISSED, with all controls
CLEAN (`results/scratch-b3-unannot-valgrind-full/`). Case 4 under the SQLite
layers exited
with an ASan-handled SEGV but no boundary report, so the harness correctly
classified it as `MISSED crashed SEGV` rather than claiming detection. This
is not an x86-64 lab result and is not report evidence. The lab Valgrind run
is tracked separately.

The Arena/Free-list annotation arms retain their CMA layout. ASan manual
poisoning makes requested-size slack and freed objects inaccessible, and
Valgrind's mempool requests restore object ownership information. Neither
address-based annotation can distinguish a stale pointer once the same
address belongs to a new object (case 10). Rewriting to libc is effective
for ordinary overflow and pre-reuse UAF, but may remove the phenomenon one
wanted to study, especially deterministic slot reuse or bulk lifetime end.

The complete local 16-case comparison on 2026-11-10 was:

| Tool | Arm | DETECTED | MISSED | UNSUPPORTED | Controls |
|---|---|---:|---:|---:|---:|
| ASan | Arena, unannotated | 2 | 12 | 2 | 16 CLEAN |
| ASan | Arena, annotated | 11 | 3 | 2 | 16 CLEAN |
| ASan | Free list, unannotated | 2 | 14 | 0 | 16 CLEAN |
| ASan | Free list, annotated | 12 | 4 | 0 | 16 CLEAN |
| ASan | either rewrite | 12 | 1 | 3 | 16 CLEAN each |
| Valgrind | Arena, unannotated | 2 | 12 | 2 | 16 CLEAN |
| Valgrind | Arena, annotated | 13 | 1 | 2 | 16 CLEAN |
| Valgrind | Free list, unannotated | 2 | 14 | 0 | 16 CLEAN |
| Valgrind | Free list, annotated | 14 | 2 | 0 | 16 CLEAN |
| Valgrind | either rewrite | 13 | 0 | 3 | 16 CLEAN each |

ASan ran on macOS arm64; Valgrind 3.19.0 ran in a local Linux arm64
container. The tools and hosts differ, so these are development checks and
cannot replace a same-VM detection matrix. Case 3 remains MISSED after the
rewrite under ASan because the far write lands in a different live object.
The rewrite's cases 10, 12 and 15 lose their defining precondition. For the
Free list, annotations preserve cases 10 and 15 as valid experiments, even
when the detector misses the stale pointer after immediate reuse.

## When rewrite is feasible

A thin wrapper whose users already call `free` for every object is easy to
rewrite. Arena users that rely on bulk destruction need ownership changes at
call sites, otherwise `st_alloc_fini` no longer frees their objects. A
thread-local pools also rely on thread ownership and cheap local allocation;
replacing them with global libc calls changes synchronization and contention.
A database's memsys5 or lookaside layer can be disabled by configuration, but
that also changes allocation size classes, memory limits, OOM behavior and
reuse. For the real SQLite cases, A's `rewrite` arm disables memsys5 and
lookaside rather than patching SQLite's source. That is a valid detection
comparison only with those semantic differences stated.

## Performance protocol

`benchmarks/allocator-churn/run.sh` runs identical source operations for
Arena, Free list, their annotated builds, and both rewrite arms. It writes
the same CSV schema as C's benchmarks, with five repetitions, wall time and
peak RSS. Compare annotation on/off within the same allocator and tool;
compare rewrite separately because it changes the allocation algorithm.
The final Part B numbers come from one x86-64 EC2 VM, but C's earlier
`speedtest1` numbers came from a different VirtualBox VM and must be
reported separately. C's existing 3.50.4 memsys5 performance data have no
custom annotations; they do not answer annotation overhead by themselves.

The final EC2 [benchmark bundle](../results/2026-11-10-allocator-churn-IkUTIU/benchmark.csv)
has 90 successful runs. Five-run median workload seconds and annotation
on/off ratios are:

| Allocator | ASan off → on | Valgrind off → on | Rewrite ASan / Valgrind |
|---|---:|---:|---:|
| Arena | 1.510 → 1.582 (1.05×) | 2.273 → 4.038 (1.78×) | 0.547 / 2.672 |
| Free list | 1.478 → 1.625 (1.10×) | 2.413 → 5.209 (2.16×) | 0.535 / 2.686 |

The rewrite changes allocation and lifetime semantics. Its performance
numbers are therefore a separate tradeoff, not an annotation overhead
estimate. The formal report table also gives peak RSS.

An arm64 Linux Docker development run of five repetitions at 10000 cycles
produced the following **provisional** medians (seconds; high-resolution
workload wall time):

| Allocator | ASan off → on | Valgrind off → on | Rewrite ASan / Valgrind |
|---|---:|---:|---:|
| Arena | 0.605 → 0.675 (1.12×) | 1.019 → 1.667 (1.64×) | 0.293 / 1.669 |
| Free list | 0.594 → 0.635 (1.07×) | 1.343 → 3.168 (2.36×) | 0.447 / 2.811 |

The raw bundle is `results/scratch-2026-11-10-allocator-churn-BSCa5b/`.
Some runs overlapped with compilation in other containers, so these figures
are for workflow validation only. The EC2 run above is the final B dataset.
