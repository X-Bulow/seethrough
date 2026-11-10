# Part B draft: CMA implementation, annotations and Q1

## CMA implementations

The constructed corpus calls one `st_alloc` interface. The malloc baseline
delegates every object to libc. Arena carves 16-byte-aligned objects from a
single backing block and never reuses an individually freed object. Its
external side table records requested size and liveness so annotation can
close each object's addressable range, and `realloc` copies into a new slot.
The Free list uses 32, 64, 128 and 256-byte classes, plus non-recycled larger
slots, all within one backing block. Freeing a class slot immediately puts it
at the head of a LIFO list. Bookkeeping for the next free slot occupies the
slot only while it is free.

SQLite provides two additional unannotated CMA layers for the constructed
corpus. memsys5 uses a single supplied heap and power-of-two buddy blocks;
lookaside uses 128-byte slots owned by an in-memory database connection.
Requests too large for lookaside fall back to SQLite's global allocator. The
adapter uses SQLite 3.53.3; the real-bug corpus uses 3.22.0 and C's
`speedtest1` benchmark uses 3.50.4. Their measurements are labelled by
version and are not pooled.

## Boundary annotations

`ST_ANNOT=1` changes annotation calls in Arena and Free list. ASan
poisons the backing block, unpoisons exactly the requested bytes at allocation
and re-poisons at free. Memcheck's mempool requests describe each logical
allocation and free. The Free list temporarily opens the in-slot next link
while maintaining its list. Both allocators have clean negative controls in
the local development matrix. The generated memsys5 patch applies the same
idea to SQLite buddy blocks and temporarily opens free-list links. The
`st_alloc` adapter tracks exact requests to close memsys5's rounded slack.
Lookaside has no verified annotation patch; its `ANNOT=1` build is rejected.
In the complete local memsys5 annotated matrix, ASan detected 11 of 16
defects and Valgrind detected 14 of 16, with all 32 negative controls CLEAN.
The unannotated memsys5 and lookaside arms each detected 1/16 under ASan
and 2/16 under Valgrind, with clean controls. Valgrind's two unannotated
detections concerned the outer pool boundary and the ended pool lifetime,
not the individual SQLite object boundary.
The two tools ran on different arm64 development environments, so these
counts must be confirmed on the common x86-64 lab VM before citation.

## Rewrite and Q1 interpretation

The two 14-line rewrite arms replace pool operations with libc
`malloc`/`free`/`realloc`. They expose each object to ASan and Memcheck, but
change reuse, reclamation and pool-destruction semantics. A detected overflow
or UAF in a rewrite arm shows that the detector sees a libc object boundary;
it does not show that it understood the original CMA. Cases whose defining
event disappears are `UNSUPPORTED`, not `MISSED` or `DETECTED`.

For the 2026-11-10 **development** ASan full 16-case matrix, each SQLite
layer produced 1 DETECTED and 15 MISSED bug rows, while each rewrite arm
produced 12 DETECTED, 1 MISSED and 3 UNSUPPORTED rows. All 64 negative
controls were CLEAN. The one detected SQLite row was use-after-pool-destroy;
its other rows were hidden by the pool or did not produce an ASan boundary
report. The rewrite's MISSED row (case 3) jumped into another live object,
so even libc object boundaries could not identify it as an invalid access.
Cases 10, 12 and 15 lost their required reuse or bulk-free precondition
under rewrite and were marked UNSUPPORTED. These are macOS arm64 observations,
not final x86-64 results. Formal VM results should replace this paragraph
before submission. See `docs/cma-rewrite.md` for the semantic comparison and
performance protocol.

For Arena and Free list specifically, annotations changed ASan detection
from 2/14 eligible to 11/14 in Arena and from 2/16 to 12/16 in Free list.
Under Valgrind, the corresponding counts rose from 2/14 to 13/14 and from
2/16 to 14/16. Each rewrite detected 12/13 eligible cases under ASan and
13/13 under Valgrind, while making three original pool cases inapplicable.
The full local table and per-case interpretation are in `docs/cma-rewrite.md`.

The mechanism explains the remaining gaps. A write that lands in another
live object is addressable even when both object bounds are annotated (case
3). After a Free-list slot is reissued, the old and new pointers have the
same address, so ASan and Memcheck cannot identify the old owner (case 10).
ASan's poisoning API has no free-ownership event, leaving double and
interior frees invisible when they do not access poisoned bytes (cases 13
and 14). Memcheck's mempool ownership requests detect those frees. A
whole-pool free is detected even without per-object annotations because the
single underlying malloc block itself ends (case 12); that result must not
be credited as CMA-aware detection.

The provisional five-run arm64 Docker churn benchmark measured annotation
on/off time ratios of 1.12× (Arena ASan), 1.64× (Arena Valgrind), 1.07×
(Free-list ASan) and 2.36× (Free-list Valgrind). These runs overlapped with
other compilation and must be repeated alone on C's x86-64 VM. The final
report should use those same-VM medians and RSS values instead.
In the same development bundle, rewrite reduced ASan workload time for
Arena (0.675 to 0.293 s) and Free list (0.635 to 0.447 s), while raising
ASan peak RSS from roughly 45–47 MiB to about 157 MiB. The rewrite and
annotated arms have different allocation algorithms, so this is a workload
tradeoff rather than an isolated annotation cost.
