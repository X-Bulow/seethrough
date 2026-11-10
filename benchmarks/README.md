# benchmarks — Q2 overhead (Part C)

| directory | program | why it is here | CMA switch |
|---|---|---|---|
| `sqlite-speedtest1/` | SQLite `speedtest1` | the proposal's main benchmark; memsys5 and lookaside are compile/config switches | `-DSQLITE_ENABLE_MEMSYS5` + `SQLITE_CONFIG_HEAP`; lookaside via `SQLITE_CONFIG_LOOKASIDE` |
| `postgres/` | a regression subset | memory contexts (aset / slab) | none upstream; the rewrite question is "what would it cost" |
| `lua/` | fixed Lua allocation/sort/GC workload | independent interpreter overhead benchmark | original Lua allocator; no CMA switch in this experiment |

Protocol (from the proposal, kept): `-O2`, median of 5 runs, wall-clock time and peak RSS
(`/usr/bin/time -v`, `Maximum resident set size`), baseline uninstrumented, then each tool,
then each tool with annotations on. One CSV per benchmark, columns:
`bundle, benchmark, config, tool, annot, run, seconds, peak_rss_kb`. `plot.py`
draws the figures from the CSVs and nothing else.

## 性能图（C5.6）

在仓库根目录执行（Python 3 + matplotlib）：

Ubuntu 26.04 若提示缺少 `ensurepip`，先执行 `sudo apt install python3.14-venv`，再重试下列命令。

```bash
python3 -m venv build/plot-venv
build/plot-venv/bin/python -m pip install -r benchmarks/requirements.txt
build/plot-venv/bin/python benchmarks/plot.py
```

默认读取 `results/*/benchmark.csv`，仅允许同一 benchmark。结果目录同时包含 SQLite 和 Lua 时，须显式指定同一 benchmark 的一份或多份 CSV：

```bash
build/plot-venv/bin/python benchmarks/plot.py results/2026-11-05-sqlite-speedtest1-A3VkNv/benchmark.csv results/2026-11-05-sqlite-speedtest1-memsys5-LGSfcu/benchmark.csv
```

输出为 `report/figures/benchmark-performance.{png,pdf}`（耗时及峰值 RSS）、
`report/figures/benchmark-overhead.{png,pdf}`（相对各自 baseline 的倍数），
以及 `report/tables/benchmark-summary.csv`。PDF 可直接用于报告。

每个 bundle、配置、annotation 和工具分别取 5 次运行的中位数；RSS 从 KiB 换算为 MiB。
脚本检查运行编号恰为 1–5，保持不同 bundle 的结果独立，缺少同组 baseline 时直接报错。
倍数是工具中位数除以 baseline 中位数，不能用较低的开销推断较好的检测能力。
