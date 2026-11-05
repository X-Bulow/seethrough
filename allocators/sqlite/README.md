# sqlite — memsys5 and lookaside as allocator layers (B3)

Plan:
1. SQLite amalgamation **3.53.3** (capstone's general-port pin; sqlite3.c sha256 `87497ab6...`), fetched by `tools/fetch-sqlite.sh 3.53.3` into `vendor/` (gitignored, hash-checked, never committed). The real-bug corpus in `corpus/real/` uses 3.22.0 instead, because those bugs are only live there; memsys5 and lookaside are unchanged in substance between the two, and the report says which version each table used.
2. Build with `-DSQLITE_ENABLE_MEMSYS5` and `sqlite3_config(SQLITE_CONFIG_HEAP, buf, size, min)` in `st_alloc_init`, so `st_alloc` = `sqlite3_malloc` and the object comes from memsys5's static heap.
3. Lookaside: open an in-memory database with `SQLITE_CONFIG_LOOKASIDE` and allocate through `sqlite3DbMallocRaw` (internal; needs the amalgamation built with `SQLITE_PRIVATE` removed, or a small shim compiled into the amalgamation).
4. Annotations: memsys5 has none upstream. Add `ST_POISON`/`ST_UNPOISON` in `memsys5Malloc`/`memsys5Free` under `ST_ANNOT` and record the patch as `memsys5-annot.patch`.
5. Rewrite arm: build without `SQLITE_ENABLE_MEMSYS5` and without `SQLITE_CONFIG_HEAP`; `sqlite3_malloc` is then a thin wrapper over malloc. That is the professor's "undo the CMA" with zero lines changed in our code.

Layout facts (to verify): memsys5 is a power-of-two buddy allocator; a 24-byte request gets a
32-byte block; blocks of one size are adjacent; freed blocks are coalesced with buddies and
reused; no header inside the block (control bytes live in a separate array).
