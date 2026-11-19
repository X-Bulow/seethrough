# Experiment environment record

Each results bundle includes `env.txt`. This table summarizes the platforms and tool versions needed to interpret or reproduce the committed measurements.

| Item | Value | Date |
|---|---|---|
| Server | Lab VirtualBox x86-64 Linux VM; AMD Ryzen 7 3700X, 4 visible logical CPUs, approximately 7.25 GiB RAM | 2026-11-07 |
| Kernel | `7.0.0-38-generic`; LAM is not exposed and the tagged address ABI required by HWASan is unavailable | 2026-11-07 |
| Distribution / glibc | Ubuntu 26.04 LTS / glibc 2.43 (`2.43-2ubuntu2.4`) | 2026-11-07 |
| clang | 21.1.8 (`1:21.1.8-6ubuntu1`, Ubuntu package; installation method not recorded) | 2026-11-07 |
| gcc | 15.2.0 (`15.2.0-16ubuntu1`) | 2026-11-07 |
| valgrind | 3.26.0 (`1:3.26.0-0ubuntu1`) | 2026-11-07 |
| Detection server (formal ASan and Valgrind results) | LXD container on lab server pinwheel12; Intel Xeon Gold 6230, 76 logical CPUs; Ubuntu 26.04.1 LTS (upgraded from 18.04 on 2026-11-13), glibc 2.43 (`2.43-2ubuntu2.7`); shared host kernel `6.12.111+deb13-amd64`, `lam: 0`; clang 21.1.8, gcc 15.2.0, valgrind 3.26.0, matching the VM versions above | 2026-11-13 |
| HWASan | Cannot run on the lab x86-64 VM without LAM; run instead in a Lima aarch64 VM on an Apple M5 Mac: Ubuntu 26.04.1, kernel 7.0.0-38 (7.0.0-43 for the formal 2026-11-13 bundle), clang 21.1.8 + lld 21.1.8; requires `-fuse-ld=lld`. See [hwasan.md](hwasan.md). x86-64 aliasing mode runs on the lab server (Xeon Gold 6230, no LAM), but does not check heap blocks above 64 KiB or see inside allocator pools, so it was excluded | 2026-11-13 |
| LowFat | Commit `20f8075`; clang 4.0.0 built in Ubuntu 18.04 Docker / glibc 2.27; writes across allocation boundaries detected, see [lowfat.md](lowfat.md) | 2026-11-09 |
| SQLite | 3.50.4 amalgamation；memsys5：`-DSQLITE_ENABLE_MEMSYS5` | 2026-11-07 |
| PostgreSQL / Lua / CPython | Lua 5.4.9: baseline, ASan, and Valgrind measured; PostgreSQL and CPython not tested | 2026-11-08 |
| Optimization | Detection defaults to `-O0 -g`; performance uses `-O2 -g -fno-omit-frame-pointer`, with `-fsanitize=address` added for ASan | 2026-11-07 |
