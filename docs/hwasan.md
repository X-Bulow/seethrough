# HWASan 可行性（Week 1 必须填）

- 日期：2026-11-05（记录日期）
- 机器：实验环境为 VirtualBox 中的 Ubuntu 26.04（x86-64）；CPU：未记录；内核：`7.0.0-38-generic`；`grep -c lam /proc/cpuinfo`：`0`
- clang 版本：`Ubuntu clang version 21.1.8 (6ubuntu1)`
- 编译命令：`clang -fsanitize=hwaddress -O0 -g corpus/controls/positive-uaf.c -o positive-uaf && ./positive-uaf`（实际通过 `bash tools/hwasan-check.sh` 执行，输出路径由脚本指定）
- 结果：编译成功，运行失败：`FATAL: HWAddressSanitizer requires a kernel with tagged address ABI.`，退出码 `99`。
- 若原生失败，备选 A（aarch64 交叉 + qemu-user）的结果：QEMU 10.2.1 下普通 ARM64 程序运行成功；HWASan 程序编译成功，但运行报 `Illegal instruction`，首次退出码 `124`；使用 `-cpu max` 重试仍失败，退出码 `137`。未获得 HWASan 检测报告，原因尚未确定。
- 若原生失败，备选 B（Apple Silicon 上的 aarch64 Linux VM）的结果：未测试；本轮不再投入该路线，不对其可行性作判断。
- 最终结论（2026-11-06，C3.4）：HWASan 在本项目已测试的环境中未能成功运行，本轮不再投入。当前 x86-64 VM 未暴露 LAM，且运行时明确报告缺少 tagged address ABI；aarch64 + QEMU 路线也未通过运行验证，具体失败原因尚未确定。该结论仅适用于上述已测试配置，不代表 HWASan 在其他主机或 aarch64 Linux 上不可用。
- 实验处理：本轮不生成 HWASan 的检测 verdict 或性能 overhead；检测矩阵中若保留 HWASan 配置，应标为 `UNSUPPORTED` 并引用上述环境限制，不能把运行失败记为 `MISSED`。未通过 positive control，不能据此评价检测能力。
- 环境差异：其他已记录的工具实验运行于 x86-64 Ubuntu VM；备选 A 使用 aarch64 交叉编译和 QEMU 用户态模拟。由于 HWASan 未成功运行，不进行跨环境性能比较，也不开展依赖其可行性的 tag 粒度实验。
