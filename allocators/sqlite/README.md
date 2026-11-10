# SQLite allocator layers (B3)

The constructed corpus uses the pinned SQLite **3.53.3** amalgamation from
`tools/fetch-sqlite.sh`. The real SQLite bug corpus uses 3.22.0; C's
`speedtest1` benchmark uses 3.50.4. Do not combine their measurements as
one-version data.

| `ALLOC` | Path to user object | Layout | Reuse |
|---|---|---|---|
| `memsys5` | `st_alloc` → `sqlite3_malloc64` → SQLite memsys5 | The heap is a single `malloc` block. memsys5 divides it into power-of-two buddy blocks, with control bytes in a separate region of that heap. Minimum block is 16 bytes in this arm; a 24-byte request occupies 32 bytes. | Freed buddies can coalesce; the next request may reuse the same address, but reuse is not guaranteed. |
| `lookaside` | `st_alloc` → SQLite's internal `sqlite3DbMallocRaw` on an in-memory database | 8192 external 128-byte lookaside slots; a request larger than a slot falls back to SQLite's global allocator. Slot bookkeeping is in the slot while free. | A freed slot is pushed onto a free list and is normally returned by the next fitting request. |

The lookaside arm links the amalgamation with `SQLITE_PRIVATE=` to export
`sqlite3DbMallocRaw` and two companion internal functions. This is a
deliberately narrow test adapter, not a public SQLite extension. The
amalgamation is compiled once per tool/annotation arm and reused across the
16 cases. `st_alloc_fini` releases the
database and backing buffer and is idempotent in both arms.

The memsys5 arm also has `ANNOT=1`. `patch_memsys5.py` applies the recorded
`memsys5-annot.patch` to a generated copy under `build/`; the pinned source in
`vendor/` stays unchanged. ASan poisons the pool, opens a buddy block at
allocation and closes it at free. Memcheck receives a mempool allocation and
free for each buddy block. SQLite stores free-list links inside free blocks,
so the patch temporarily opens exactly those links during link/unlink. The
adapter separately closes the rounding slack beyond each `st_alloc(n)`
request. This is necessary for a 24-byte request to expose its 32-byte buddy
block's final 8 bytes as invalid to the constructed corpus. Internal SQLite
allocations have only rounded-block precision because their original request
size is not passed through the adapter.

Lookaside remains `ANNOT=0` only: its free-list links and fallback path need
a separate verified patch. The build rejects `ANNOT=1` for lookaside rather
than presenting an unannotated run as annotated. C5.3 can use the Arena and
Free-list annotation comparison without this optional lookaside arm.

Development verification on 2026-11-10: all 16 memsys5 annotated cases and
controls ran under ASan on macOS arm64 and Valgrind 3.19.0 in a Linux arm64
container. ASan reported 11/16 defects, Valgrind 14/16, and all 32 negative
controls were CLEAN. These are not the final x86-64 VM measurements. The
raw bundles are `results/scratch-b3-memsys5-annot-asan-cached/` and
`results/scratch-b3-memsys5-annot-valgrind-cached/`.

Unannotated memsys5 and lookaside each produced 1/16 ASan detections and
2/16 Valgrind detections; all 64 controls were CLEAN for the two tools.
Valgrind saw cases 4 (past the entire pool) and 12 (after pool destruction).
ASan saw case 12; case 4 ended in a signal without a boundary report on this
host and was classified MISSED crashed SEGV. The local Valgrind bundle is
`results/scratch-b3-unannot-valgrind-full/`.
