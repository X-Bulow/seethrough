# HWASan 可行性（Week 1 必须填）

- 日期：
- 机器：实验室 x86-64 服务器，CPU：  内核：  `grep -c lam /proc/cpuinfo`：
- clang 版本：
- 编译命令：`clang -fsanitize=hwaddress -O0 -g corpus/controls/positive-uaf.c -o positive-uaf && ./positive-uaf`
- 结果：（粘贴 HWASan 报告的前 20 行，或者编译 / 运行错误信息）
- 若原生失败，备选 A（aarch64 交叉 + qemu-user）的结果：
- 若原生失败，备选 B（Apple Silicon 上的 aarch64 Linux VM）的结果：
- 结论：可行（方式：）/ 不可行（原因：）
- 若可行：tag 粒度 16 字节，对 1 字节 overflow 的 case 需要注意什么；和其他 tool 的环境差异怎么在报告里说明
