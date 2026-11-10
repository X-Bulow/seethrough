# What the allocator annotations describe

Both allocators use the same `st_alloc` interface and the same source for annotated and
unannotated builds. `ST_ANNOT=0` makes every macro in `st_annot.h` a no-op. `ST_ANNOT=1`
activates ASan's manual poison/unpoison calls for ASan builds, or Valgrind's mempool and
addressability requests for Memcheck builds. Allocator bookkeeping is kept outside live
objects, except for the free-list next link stored inside a freed slot.

| Boundary or mistake | Arena with annotations | Free list with annotations | Limit |
|---|---|---|---|
| Requested size and alignment slack | ASan poisons the pool then unpoisons exactly `n` bytes; Memcheck allocates a mempool object of `n` bytes | Same, per slot | An overflow that jumps into another **live** object is addressable again (case 3). |
| Free before reuse | Side-table size lets ASan re-poison the old object and Memcheck issue `MEMPOOL_FREE` | Slot size lets both requests close the object | Without annotations, the backing block stays live to the tools (cases 8 and 9). |
| Reuse | Arena never reuses before pool destruction | LIFO reuse opens the same address for the new owner | Address-based annotations cannot tell a stale pointer from the new pointer once storage is reissued (case 10). |
| Ownership errors at `st_free` | Memcheck can report an invalid or repeated `MEMPOOL_FREE` | Same | ASan poison/unpoison alone cannot report a free call with no invalid memory access (cases 13 and 14). |
| Whole-pool destruction | Underlying `free` ends the backing block | Same | A tool report here is about the outer block, not per-object tracking (case 12). |

The Arena needs an external size/liveness table to re-poison a freed object without adding a
header between objects. This is a design cost of annotation: the original no-op `st_free`
could not report cases 8 and 9. The table is present in both `ST_ANNOT` configurations, so
the annotated-versus-unannotated comparison changes only the tool requests. The Free list
temporarily opens its in-slot next link while maintaining the list, then closes the slot again;
otherwise allocator-internal reads would be misreported as user defects. Its `st_realloc`
always moves, preserves the prefix, and ends the old slot's lifetime.

## SQLite memsys5 extension

The optional B3 memsys5 arm uses a generated patch against pinned SQLite
3.53.3. The patch tracks rounded buddy blocks with ASan poison/unpoison and
Valgrind mempool requests. It opens each in-band free-list link only while
SQLite reads or writes it, then closes it. The adapter's side table tracks
the exact `st_alloc(n)` request and poisons the remaining size-class slack;
without it, a 24-byte request's `p[24]` lies inside a valid 32-byte buddy
block. SQLite's own internal allocations retain rounded-block precision.
Lookaside has no verified annotation arm.

## Development checks, not report data

On 2026-11-07, the two positive controls were DETECTED under ASan and Valgrind. All 16
Free-list cases had CLEAN negative controls under ASan with annotations off and on. The
Valgrind run covered all 16 cases for both Arena and Free list, both annotation settings;
all negative controls were CLEAN. The raw development bundles are under
`results/scratch-stage2-*` and are gitignored. ASan ran on macOS arm64; Valgrind 3.19.0 ran
in a local arm64 Linux container. Neither is the project's citable x86-64 server environment.

The development checks exposed two corpus predictions to revisit with A. ASan did not report
an interior-pointer free in the annotated Free list (case 14): poisoning tracks access, not
ownership. Arena cases 8, 9 and 11 changed after size tracking and `realloc` were implemented;
annotated ASan and Memcheck now report their stale accesses. The annotated Arena also lets
Memcheck report double and interior frees through `MEMPOOL_FREE`.

Case 4 initially used `pool_bytes + 64`, which landed exactly in an adjacent valid metadata
allocation under Valgrind and appeared as a miss. The corpus now uses `pool_bytes + 8192`;
both ASan and Valgrind reported the outer-block over-read in local reruns. This offset still
needs confirmation on the official server because the surrounding address space can differ.
