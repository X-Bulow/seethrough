# C 部分复现检查

- 记录日期：2026-11-08；记录人：C。
- 环境：实验室 VirtualBox Ubuntu 26.04 x86-64，沿用已有工具环境。
- 起点：从远程仓库新 clone 到 `~/cs5439/P2/seethrough-repro`，checkout `342408b`；初始 `git status --short` 无输出。

| 步骤 | 结果 |
|---|---|
| `bash tools/setup-server.sh` | 三个固定版本包已安装，跳过安装并生成 `tools/VERSIONS.txt` |
| `bash benchmarks/sqlite-speedtest1/fetch.sh` | 下载 SQLite 3.50.4 源码并解压成功 |
| `bash benchmarks/sqlite-speedtest1/build.sh` | 默认 / memsys5 的 baseline、ASan 共四个二进制编译完成；有 SQLite 源码的 const 类型警告 |
| `bash benchmarks/sqlite-speedtest1/run.sh` | baseline、ASan、Valgrind 各 5 次全部完成，共 15 条 CSV 数据 |
| `bash benchmarks/sqlite-speedtest1/run-memsys5.sh` | baseline、ASan、Valgrind 各 5 次全部完成，共 15 条 CSV 数据 |
| `benchmarks/plot.py` | 使用新生成的两份 CSV，成功输出汇总及四个图表文件 |

本轮归档的结果目录（含 CSV、环境记录及逐次运行日志）：

- [默认配置](../results/2026-11-07-sqlite-speedtest1-HfnjGz/benchmark.csv)：`results/2026-11-07-sqlite-speedtest1-HfnjGz/`
- [memsys5 配置](../results/2026-11-07-sqlite-speedtest1-memsys5-L94SoN/benchmark.csv)：`results/2026-11-07-sqlite-speedtest1-memsys5-L94SoN/`

两份 bundle 共 30 次运行的退出码均为 0，CSV 中的耗时和 peak RSS 与原始 `.time` 文件一致。

绘图时首次创建 venv 因缺少 `ensurepip` 失败；安装 `python3.14-venv` 后重试成功。绘图环境为 Python 3.14、matplotlib 3.11.2，命令如下：

```bash
python3 -m venv build/plot-venv &&
build/plot-venv/bin/python -m pip install -r benchmarks/requirements.txt &&
build/plot-venv/bin/python benchmarks/plot.py \
  results/2026-11-07-sqlite-speedtest1-HfnjGz/benchmark.csv \
  results/2026-11-07-sqlite-speedtest1-memsys5-L94SoN/benchmark.csv \
  --out-dir build/repro-figures \
  --summary build/repro-summary.csv
```

输出为 `build/repro-summary.csv` 和 `build/repro-figures/benchmark-{performance,overhead}.{png,pdf}`。原始结果 bundle 已同步到本仓库；图表保留在 Ubuntu 复现 clone 的 `build/` 下，可使用上述命令重新生成。

结论：C 部分从干净 clone 下载、编译、性能运行及绘图的流程已跑通。这次没有重新运行 Detection Matrix，D4 整体仍未完成。
