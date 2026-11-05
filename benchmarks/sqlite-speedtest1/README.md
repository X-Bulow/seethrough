# SQLite speedtest1

SQLite 3.50.4，实验环境为 VirtualBox Ubuntu 26.04 x86-64。

## 复现

在仓库根目录依次执行以下命令。
已有源码和二进制时，可跳过下载和编译。

    bash benchmarks/sqlite-speedtest1/fetch.sh
    bash benchmarks/sqlite-speedtest1/build.sh
    bash benchmarks/sqlite-speedtest1/run.sh
    bash benchmarks/sqlite-speedtest1/run-memsys5.sh

下载源码和编译产物放在忽略的 build/ 目录，不提交。

## 方法

- 编译参数为 -O2 -g -fno-omit-frame-pointer。
- ASan 增加 -fsanitize=address；Valgrind 使用对应 baseline。
- 工作负载为 --memdb --size 100 --testset main。
- memsys5 增加 -DSQLITE_ENABLE_MEMSYS5，使用 --heap 268435456 64。
- 每组五次，分别取耗时和峰值 RSS 的中位数。
- 所有配置均无自定义分配边界标注。
- Valgrind 的 RSS 包含工具自身开销。

## 结果

倍数相对于同配置的 baseline。

| 配置 | 工具 | 耗时 s | 耗时倍数 | RSS MiB | 内存倍数 |
|---|---|---:|---:|---:|---:|
| 默认 | Baseline | 2.30 | 1.00 | 77.05 | 1.00 |
| 默认 | ASan | 6.08 | 2.64 | 611.45 | 7.94 |
| 默认 | Valgrind | 62.04 | 26.97 | 189.70 | 2.46 |
| memsys5 | Baseline | 2.47 | 1.00 | 121.16 | 1.00 |
| memsys5 | ASan | 5.34 | 2.16 | 166.52 | 1.37 |
| memsys5 | Valgrind | 60.58 | 24.53 | 208.29 | 1.72 |

原始结果位于 results/ 下：

- 2026-11-05-sqlite-speedtest1-A3VkNv/
- 2026-11-05-sqlite-speedtest1-memsys5-LGSfcu/

结果描述当前环境的性能，检测能力需结合漏洞测试判断。
