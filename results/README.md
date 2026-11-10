# results

One directory per run: `YYYY-MM-DD-<label>/` with `env.txt`, `matrix.csv` (`real.csv` for `corpus/real/`, or the benchmark
CSV) and the raw `.stdout` / `.stderr` of every run. Written by `harness/run-matrix.py`, `harness/run-real.py` or
`benchmarks/*/run.sh`, committed as-is, never edited.

| bundle | what | status |
|---|---|---|
| [2026-11-10-ec2-b-pilot/](2026-11-10-ec2-b-pilot/) | EC2 positive-control pilot, case 0 malloc under ASan and Valgrind | complete; 4 rows, 2 CLEAN controls |
| [2026-11-10-ec2-b-core/](2026-11-10-ec2-b-core/) | EC2 malloc, Arena and Free list; annotation off/on; ASan and Valgrind | complete; 384 rows, 192 CLEAN controls |
| [2026-11-10-ec2-b-memsys5/](2026-11-10-ec2-b-memsys5/) | EC2 SQLite 3.53.3 memsys5; annotation off/on | complete; 128 rows, 64 CLEAN controls |
| [2026-11-10-ec2-b-lookaside/](2026-11-10-ec2-b-lookaside/) | EC2 SQLite 3.53.3 lookaside, unannotated | complete; 64 rows, 32 CLEAN controls |
| [2026-11-10-ec2-b-rewrite/](2026-11-10-ec2-b-rewrite/) | EC2 Arena and Free-list libc rewrites | complete; 128 rows, 64 CLEAN controls |
| [2026-11-10-allocator-churn-IkUTIU/](2026-11-10-allocator-churn-IkUTIU/) | EC2 annotation overhead and rewrite performance | complete; 90 successful runs, five per setting |

The five EC2 B bundles above use commit `2763402`, Ubuntu 26.04 x86-64,
clang/ASan 21.1.8 and Valgrind 3.26.0. The four full detection bundles
have 352 bug rows and 352 paired controls. All controls are CLEAN; there
are no `TOOL-ERROR` or `FALSE-POSITIVE` verdicts. See
[Part B report](../report/part-b.md) for counts and interpretation. The EC2
performance bundle is separate from C's VirtualBox benchmark bundles below.

`scratch-*/` bundles are gitignored: laptop smoke runs go there and never into the table.

A superseded bundle stays and gets a line here saying what replaced it and why.

## SQLite speedtest1（2026-11-05）

SQLite 3.50.4，VirtualBox Ubuntu 26.04。
统一使用 --memdb --size 100 --testset main。
每组 baseline、ASan、Valgrind 各运行五次，无自定义分配边界标注。

| bundle | 配置 | 状态 |
|---|---|---|
| 2026-11-05-sqlite-speedtest1-A3VkNv/ | SQLite 默认配置 | 已完成，共 15 次 |
| 2026-11-05-sqlite-speedtest1-memsys5-LGSfcu/ | memsys5，256 MiB 池，最小分配 64 字节 | 已完成，共 15 次 |

统计摘要和复现命令见 benchmarks/sqlite-speedtest1/README.md。
