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
