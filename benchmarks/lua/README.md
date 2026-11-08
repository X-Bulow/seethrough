# Lua benchmark（C5.5）

Lua 5.4.9，使用原版分配器。此扩展测量解释器的工具开销，不替换 `lua_Alloc`。
源码来自 https://www.lua.org/ftp/lua-5.4.9.tar.gz，SHA-256 为
`2335b6c582a52654f94612bf10d2f4672805d05329aa6568b1d8cd9e5c6fb8e6`。

已在实验 VM 验证 baseline 和 ASan 编译、启动成功：

- 两者使用 clang，`-O2 -g -fno-omit-frame-pointer`。
- ASan 的编译及链接均增加 `-fsanitize=address`。
- Valgrind 使用 baseline 二进制。
- 二进制分别保存为 `build/lua/bin/lua-baseline`、`build/lua/bin/lua-asan`。

固定工作负载为 `workload.lua`：默认 20 轮，每轮创建 100000 个含字符串的表，
按 id 排序、计算校验值，然后进行完整垃圾回收。它是合成工作负载。
三个配置必须使用相同参数并输出相同的校验值。

```bash
build/lua/bin/lua-baseline benchmarks/lua/workload.lua
build/lua/bin/lua-asan benchmarks/lua/workload.lua
valgrind --tool=memcheck --leak-check=full --error-exitcode=99 \
  build/lua/bin/lua-baseline benchmarks/lua/workload.lua
```

实验 VM 的试运行中，三个配置均得到校验值 `6666766818777900`，Valgrind 报告
0 errors、0 leaks。单次试运行不是最终性能结果。

## 正式实验

在仓库根目录执行：

```bash
bash benchmarks/lua/build.sh
bash benchmarks/lua/run.sh
```

`build.sh` 下载、校验源码，并按上述已验证的命令分别构建两个二进制。
已有本次构建的二进制时直接执行 `run.sh` 即可。

每配置 5 次，轮流运行 baseline、ASan、Valgrind，保存 `/usr/bin/time` 的 wall time
和 peak RSS，并验证每次退出码及校验值。结果写入新的 `results/<date>-lua-<suffix>/`，
包含 `env.txt`、`benchmark.csv` 和各次 stdout、stderr、exit、time 文件。
根据试运行耗时，完整实验约需 16 分钟。

完成后用对应 CSV 生成中位数和开销图，避免与 SQLite 结果混用：

```bash
build/plot-venv/bin/python benchmarks/plot.py results/2026-11-08-lua-36YPxm/benchmark.csv \
  --out-dir report/figures/lua --summary report/tables/lua-summary.csv
```

## 结果（2026-11-08）

每项均为 5 次运行的中位数，倍数相对于 baseline。

| 工具 | 耗时 s | 耗时倍数 | RSS MiB | 内存倍数 |
|---|---:|---:|---:|---:|
| Baseline | 4.65 | 1.00 | 29.70 | 1.00 |
| ASan | 13.85 | 2.98 | 473.35 | 15.94 |
| Valgrind | 133.64 | 28.74 | 188.44 | 6.34 |

结果 bundle：[results/2026-11-08-lua-36YPxm/benchmark.csv](../../results/2026-11-08-lua-36YPxm/benchmark.csv)。
完整日志已归档：15 次退出码均为 0、校验值一致，CSV 与原始计时文件相符，
Valgrind 各次均为 0 errors、无泄漏；环境记录中的工作负载哈希与仓库文件一致。
图表和汇总由上述命令生成。

Valgrind RSS 包含工具自身内存。这个合成工作负载只支持 Lua 工具开销分析，
没有进行 CMA 开关或 annotated/unannotated 的比较。
