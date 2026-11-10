# results

One directory per run: `YYYY-MM-DD-<label>/` with `env.txt`, `matrix.csv` (`real.csv` for `corpus/real/`, or the benchmark
CSV) and the raw `.stdout` / `.stderr` of every run. Written by `harness/run-matrix.py`, `harness/run-real.py` or
`benchmarks/*/run.sh`, committed as-is, never edited.

| bundle | what | status |
|---|---|---|
| (none yet) | | |

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
