# SQLite allocator adapters

Tests SQLite 3.53.3 memsys5 and lookaside through the shared allocator interface. Lookaside supports unannotated builds only.

- [memsys5.c](memsys5.c) — buddy-allocator adapter
- [lookaside.c](lookaside.c) — connection-local allocator adapter
- [patch_memsys5.py](patch_memsys5.py) — generates annotated SQLite source
- [memsys5-annot.patch](memsys5-annot.patch) — annotation patch

The source is downloaded by [fetch-sqlite.sh](../../tools/fetch-sqlite.sh). Other experiments use different SQLite versions; keep their measurements separate.
