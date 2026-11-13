# 实验环境记录

每个 results bundle 都带一份 `env.txt`，这里是总表。没有填的格子不能出现在报告里。

| 项目 | 值 | 记录人 | 日期 |
|---|---|---|---|
| 服务器 | 实验室 VirtualBox x86-64 Linux VM；AMD Ryzen 7 3700X，4 个可见逻辑 CPU，内存约 7.25 GiB | C | 2026-11-07 |
| 内核 | `7.0.0-38-generic`；未暴露 LAM，HWASan 所需 tagged address ABI 不可用 | C | 2026-11-07 |
| 发行版 / glibc | Ubuntu 26.04 LTS / glibc 2.43（`2.43-2ubuntu2.4`） | C | 2026-11-07 |
| clang | 21.1.8（`1:21.1.8-6ubuntu1`，Ubuntu 包；安装途径未记录） | C | 2026-11-07 |
| gcc | 15.2.0（`15.2.0-16ubuntu1`） | C | 2026-11-07 |
| valgrind | 3.26.0（`1:3.26.0-0ubuntu1`） | C | 2026-11-07 |
| HWASan | 实验室 x86-64 VM 无 LAM，不能运行；改在 Apple M5 Mac 上的 Lima aarch64 VM 中运行：Ubuntu 26.04.1、内核 7.0.0-38、clang 21.1.8 + lld 21.1.8，链接需 `-fuse-ld=lld`；见 [hwasan.md](hwasan.md)。实验室服务器（Xeon Gold 6230，无 LAM）上的 x86-64 别名模式能运行，但不检查 64 KiB 以上的堆块，看不到分配器池子内部，未采用（hwasan.md 第三轮） | A | 2026-11-13 |
| LowFat | commit `20f8075`；Ubuntu 18.04 Docker / glibc 2.27 中构建 clang 4.0.0，跨分配边界写入检测通过，见 [lowfat.md](lowfat.md) | C | 2026-11-09 |
| SQLite | 3.50.4 amalgamation；memsys5：`-DSQLITE_ENABLE_MEMSYS5` | C | 2026-11-07 |
| PostgreSQL / Lua / CPython | Lua 5.4.9：baseline、ASan、Valgrind 已测；PostgreSQL、CPython 未测试 | C | 2026-11-08 |
| 编译优化 | 检测实验默认 `-O0 -g`；性能实验 `-O2 -g -fno-omit-frame-pointer`，ASan 加 `-fsanitize=address` | C | 2026-11-07 |
