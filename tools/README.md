# tools (Part C) — the lab x86-64 Linux server, native, no containers

| file | role |
|---|---|
| `setup-server.sh` | installs or builds the pinned tool versions into `$HOME/seethrough-tools` and puts them on PATH; idempotent |
| `env.sh` | prints everything a results bundle must record (CPU, kernel, LAM, tool versions, git commit) |
| `flags.mk` | per-tool CFLAGS / LDFLAGS / defines, included by the top-level Makefile |
| `fetch-sqlite.sh` | fetches one pinned SQLite amalgamation (3.53.3 for the allocator layers and speedtest1, 3.22.0 for `corpus/real/`) into `vendor/` or `$SEETHROUGH_CACHE`, sha256-checked; prints the directory |
| `hwasan-check.sh` | the Week-1 HWASan feasibility probe (C3.2); writes its findings for `docs/hwasan.md` |

Pinning without containers: `setup-server.sh` records the exact version of every tool it
installed (apt package version, or git commit + build flags for source builds) in
`tools/VERSIONS.txt`, and `env.sh` prints the versions actually found on PATH. The two must
agree in every bundle, or the bundle is not citable.
