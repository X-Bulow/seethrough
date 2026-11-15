# corpus/real — real SQLite engine defects (Tier 2, validation)

`corpus/cases/` is the matrix: bugs we wrote, with known ground truth, compiled against each
allocator. This directory asks whether those cells transfer to a real program: an actual
SQLite defect whose object already lives in SQLite's own allocator, run under the same tools.
Few cases, reported as a check on Tier 1, not as a second matrix.

## Source and version

Cases come from `capstone/bug-corpora/sqlite/engine-repros` in
[project-starch/llvm-capstone](https://github.com/project-starch/llvm-capstone) (branch `dev`,
commit 9bb68291, copied 2026-11-05): engine-internal defects reduced to one C driver each over
the **SQLite 3.22.0 amalgamation**. Each `case.c` here is the capstone file byte for byte
(sha256 in `case.json` and `PROVENANCE.md`); the port is entirely in `shared/`.

| what | value |
|---|---|
| version | 3.22.0 (`sqlite-amalgamation-3220000.zip`, sqlite.org/2018); the bugs are live only there |
| sqlite3.c sha256 | `7991acd0d8c78435d47523a43aeeb117f0aa264c4d7d0d10410f0128ed1f6004` |
| fetched by | `tools/fetch-sqlite.sh 3.22.0` into `vendor/` (gitignored, never committed); the Makefile calls it |

We build the **stock** amalgamation. Capstone's `adapt-sqlite-322.sh` rewrites alignment for
capability pointers and is not needed on x86-64; its FTS trigger patches are not needed because
no FTS case was taken. SQLite itself is never simplified: cutting the engine changes where
objects are allocated and the cell stops meaning anything. Only triggers are reduced, and
capstone already did that.

## The cases

| dir | capstone case | class | object and where it sits | fault site |
|---|---|---|---|---|
| `03-blob-close-after-db-close` | 03_e464802d49 | UAF read | the `sqlite3` connection (plain engine malloc) | `sqlite3DbFreeNN` |
| `19-rtree-cursor-stale-node` | 19_c8c9cdd9dd | UAF read | `RtreeNode`, 488 B, `sqlite3_malloc` | `nodeRelease` |
| `29-btree-get4byte-page-overread` | 29_fz02 | over-read | a page buffer (pcache1) | `sqlite3Get4byte` |
| `31-dbstat-decodepage-overflow` | 31_fz10 | over-read | a page buffer (pcache1) | `statDecodePage` |

Two temporal, two spatial; all four are among the 26 cases capstone's host-ASan reference run
reports (the six it could not, 01/04/08/09/11/13, were not candidates). Case 18, the memsys5
free-list demonstrator, was dropped: capstone withdrew it as its own positive control, and
`corpus/cases/` already covers that shape with ground truth.

## Arms (`-DST_SQLITE_ARM`, see `shared/repro322_common.h`)

| arm | engine build | what the object sits in |
|---|---|---|
| `memsys5` | `-DSQLITE_ENABLE_MEMSYS5`, lookaside 0,0; `sqlite3_config(SQLITE_CONFIG_HEAP, 256 KiB static array, min 64)` | one arena; capstone's measured arm |
| `default` | SQLite as shipped: lookaside on, pcache bulk pool on | per case: lookaside slab, pcache bulk block, or plain malloc (`case.json` `layer_by_arm`) |
| `rewrite` | no memsys5, `-DSQLITE_DEFAULT_LOOKASIDE=0,0 -DSQLITE_DEFAULT_PCACHE_INITSZ=0` | every object is its own malloc block |

`rewrite` is the configuration capstone's `shared/run-host-asan.py` uses to check that a case
makes its invalid access at all. It is the professor's "undo the CMA" with zero lines of SQLite
changed, and it is each case's positive control: `harness/run-real.py` runs asan/rewrite first
and marks the case's other rows UNSUPPORTED if it is not DETECTED. There is no negative-control
twin for a real bug.

All engine builds add `-DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION` plus the case's
`engine.flags` (rtree, dbstat, incrblob). `HAVE_MALLOC_USABLE_SIZE` is not set, so SQLite keeps
its own 8-byte size prefix on every malloc block, on every arm alike.

## Running

    make real TOOL=asan ARM=memsys5 REAL=19-rtree-cursor-stale-node        # one image, run it
    python3 harness/run-real.py --tools asan valgrind --out results/<date>-server-real

The engine is compiled once per (tool, arm, engine group) into `build/engine/`. Markers:
`ST BEGIN` / `ST READY` (engine configured, body started: weaker than in `corpus/cases/`, where
READY is printed right before the access) / `ST DONE`; each case also prints its own
reachability line (`case.json` `reached`), without which a silent run is TOOL-ERROR, not MISSED.

## Formal results (2026-11-16, lab server)

`results/2026-11-16-lab-real` (A7.5): commit `2098f2a`, Ubuntu 26.04.1 x86-64, clang 21.1.8,
Valgrind 3.26.0. Both tools passed their positive controls and every case passed the asan/rewrite
gate. LowFat was not run (out of scope since 2026-11-14, see `docs/lowfat.md`).

| case | asan memsys5 | asan default | asan rewrite | valgrind memsys5 | valgrind default | valgrind rewrite |
|---|---|---|---|---|---|---|
| 03 UAF | MISSED | DETECTED | DETECTED | MISSED | DETECTED | DETECTED |
| 19 UAF | MISSED (SEGV at 0x2) | DETECTED | DETECTED | DETECTED* (read at 0x2, then SIGSEGV) | DETECTED | DETECTED |
| 29 over-read | MISSED | DETECTED** | DETECTED | MISSED | DETECTED** | DETECTED |
| 31 over-read | DETECTED*** | DETECTED** | DETECTED | MISSED | DETECTED** | DETECTED |

\* the harness records Memcheck's invalid read at the zero page as DETECTED; it is the same crash that
ASan's signal handler reports (MISSED, crashed), caused by a pointer loaded from the stale node, and
not a report on the node. \*\* the read leaves the pcache bulk block; ASan reports it in heap redzone
memory ("wild pointer"), Memcheck in a freed or unallocated block, never against the page.
\*\*\* 34,968 bytes past the 256 KiB arena `sqlite_heap`, in the arena's own redzone (`note`: "left
the arena").

1. **The temporal cases transfer.** memsys5 hides both uses after free from both tools; where the
   object is a plain malloc block (default, rewrite) both tools report the freed block. A7.6 is
   confirmed: case 19's crash in ASan's signal handler is classified MISSED (crashed).
2. **The spatial cases depend on the stride.** Inside memsys5, case 29 stays in memory the tools
   consider valid and is missed by both; case 31 leaves the arena and ASan reports the arena's bound.
   Memcheck has no redzones around global data and misses both. In the shipped configuration both
   reads leave the bulk block. Every spatial detection outside the rewrite is a detection of the
   container. Case 29's memsys5 arm was DETECTED on the macOS dev run (1.9 KB past the arena) and is
   MISSED here: like `corpus/cases` case 4, a far stride's verdict depends on the layout.
3. **The `default` arm is two layers**, as below: for 03 and 19 the object is a plain malloc.

## What the macOS smoke run showed (dev machine, clang 17 arm64, not citable)

| case | asan memsys5 | asan default | asan rewrite |
|---|---|---|---|
| 03 | MISSED | DETECTED | DETECTED |
| 19 | MISSED, then SEGV at 0x2 | DETECTED | DETECTED |
| 29 | DETECTED, global-buffer-overflow 1.9 KB past the arena | DETECTED (wild pointer) | DETECTED |
| 31 | DETECTED, global-buffer-overflow 2.2 KB past the arena | DETECTED (wild pointer) | DETECTED |

Three things the server run must keep in mind, each written up in the case README:

1. **The temporal cases transfer.** memsys5 hides both UAFs. Case 19 then crashes on allocator
   metadata read through the stale pointer; ASan prints `SEGV on unknown address` from its
   signal handler, which `harness/classify.py` records as MISSED (crashed), not DETECTED.
2. **The two fuzz over-reads step too far to be hidden.** About 2 KB past the page, past the
   whole 256 KiB arena (and a 1 MiB one) and past the pcache bulk block. ASan reports the
   container's bound, not the page's; `run-real.py` notes "left the arena". A real spatial bug
   that stays inside the arena would need a smaller stride, which these images do not give.
3. **The `default` arm is two layers.** Which one holds the object is per case; for 03 and 19
   the object is a plain malloc and `default` detects, which is itself a result: SQLite's
   shipped configuration hides fewer of these bugs than its memsys5 configuration.

## Layout

    corpus/real/<nn>-<slug>/
        case.c          capstone's driver, unchanged
        case.json       class, access, arms, layer_by_arm, reached, engine flags, expected, capstone provenance
        PROVENANCE.md   capstone's, with our copy header
        README.md       the explanation (docs/test-programs.md headings)
    corpus/real/shared/
        repro322_common.h   our implementation of the five things a case needs; selects the arm
        repro322_memfs.c    capstone's in-memory VFS, unchanged (cases 29, 31)
