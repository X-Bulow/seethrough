# tools (Part C) — the lab x86-64 Linux server, native, no containers

| file | role |
|---|---|
| `setup-server.sh` | installs pinned Ubuntu clang/Valgrind packages, skips matching versions, and records actual versions in `tools/VERSIONS.txt` |
| `env.sh` | prints everything a results bundle must record (CPU, kernel, LAM, tool versions, git commit) |
| `flags.mk` | per-tool CFLAGS / LDFLAGS / defines, included by the top-level Makefile |
| `hwasan-check.sh` | the Week-1 HWASan feasibility probe (C3.2); writes its findings for `docs/hwasan.md` |

Pinning without containers: `setup-server.sh` records the exact version of every tool it
installed (apt package version, or git commit + build flags for source builds) in
`tools/VERSIONS.txt`, and `env.sh` prints the versions actually found on PATH. The two must
agree in every bundle, or the bundle is not citable.

Lab verification (2026-11-07): ASan and Valgrind detected the malloc heap-overflow-write
case and accepted its negative control. UBSan reported the known `int[2]` bounds probe
with `OPT="-O1 -g"`; the heap case through `st_alloc` remained unreported at that setting.
At the default `-O0`, clang warns that `object-size` has no effect. Use `OPT="-O1 -g"`
for UBSan object-size experiments and record this optimization difference. Compiler flags
remain unchanged; sanitizer runtime options are set by `harness/run-matrix.py`.
HWASan is unavailable in the tested environment (see `docs/hwasan.md`). LowFat builds and detects a write beyond allocation bounds in an Ubuntu 18.04 Docker container; its original positive controls are missed (see `docs/lowfat.md`).
