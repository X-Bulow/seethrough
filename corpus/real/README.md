# Real SQLite defects

Four SQLite 3.22.0 defects compare memsys5, default allocation, and pooling-disabled configurations. Cases originate from Capstone's engine reproductions; each case includes a provenance record.

| Case | Defect |
|---|---|
| [03](03-blob-close-after-db-close/case.c) | Blob close after connection close |
| [19](19-rtree-cursor-stale-node/case.c) | Stale rtree cursor node |
| [29](29-btree-get4byte-page-overread/case.c) | Corrupt-page over-read |
| [31](31-dbstat-decodepage-overflow/case.c) | dbstat decoding over-read |

[shared/repro322_common.h](shared/repro322_common.h) selects the engine configuration; [shared/repro322_memfs.c](shared/repro322_memfs.c) supplies the in-memory filesystem.

```bash
python3 harness/run-real.py --tools asan valgrind --out results/<new-bundle>
```

Run from the repository root. See [run-real.py](../../harness/run-real.py) for validation rules and the [results index](../../results/README.md) for measurements.
