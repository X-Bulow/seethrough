# 实验环境记录

每个 results bundle 都带一份 `env.txt`，这里是总表。没有填的格子不能出现在报告里。

| 项目 | 值 | 记录人 | 日期 |
|---|---|---|---|
| 服务器 | 实验室 x86-64 Linux：CPU 型号、核数、内存 | | |
| 内核 | `uname -r`；是否启用 LAM | | |
| 发行版 / glibc | | | |
| clang | 版本、来源（apt / 源码 / 预编译 tarball） | | |
| gcc | 版本 | | |
| valgrind | 版本 | | |
| HWASan | 方式（原生 x86-64 LAM / qemu-aarch64 / aarch64 VM）、clang 版本 | | |
| LowFat | commit、构建命令 | | |
| SQLite | 版本（amalgamation）、memsys5 编译选项 | | |
| PostgreSQL / Lua / CPython | 版本 | | |
| 编译优化 | 检测实验 -O0 -g；性能实验 -O2 | | |
