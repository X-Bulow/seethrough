<!-- seethrough: copied verbatim from capstone/bug-corpora/sqlite/engine-repros/03_e464802d49_blob_close_after_db_close/PROVENANCE.md at commit 9bb68291dcf2 on 2026-11-05. case.c is the same commit's file, sha256 23fd9ac311f4a76c8bedec548ac1887c7a7a12b054752b0b6245baf1622125e6; nothing in it was changed. -->

# blobclose -- e464802d49

Upstream fix `e464802d49`. Collected in round R1 (NVD and upstream history).

The reduction is argued in the case source's own header, reproduced here so the
claim travels with the case rather than living only in the build tree.

```
sqlite_blobclose_domain.c -- CONTROL (unprotected) reproduction of upstream
 * SQLite fix e464802d49: sqlite3_blob_close() uses a lookaside-allocated Incrblob
 * after sqlite3_close_v2() has freed its connection and the lookaside pool.
 * Public, already-fixed bug (fixed in 3.29.0); collected and reproduced for the
 * Capstone/Sublet temporal-safety study.
 *
 * CONTROL arm: SQLite's own memsys5 heap, lookaside ON, nothing revoked. On
 * unprotected Capstone the post-free access is NOT caught, so the domain RETURNS;
 * the matching host ASan build is what shows the heap-use-after-free.
```
