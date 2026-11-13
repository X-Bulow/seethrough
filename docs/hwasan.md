# HWASan 可行性

## 结论（2026-11-11）

HWASan 在实验室 x86-64 VM 上不能运行，在 Apple Silicon Mac 上的 aarch64 Linux 虚拟机中可以运行，纳入检测矩阵。链接必须用 lld（`-fuse-ld=lld`，已写入 `tools/flags.mk`）。HWASan 的结果与其他工具来自不同环境，报告中须注明；和 LowFat 使用 Docker 一样，作为例外处理。

2026-11-13 在实验室服务器上试了 clang 的 x86-64 别名模式：能运行，但只给 64 KiB 以内的堆块打标签，我们的分配器池子（1 MiB）整个不受检查，标注也不起作用，所以不用于矩阵（第三轮）。

## 第一轮：实验室 x86-64 VM 与备选 A（2026-11-05/06，记录人：C）

- 机器：VirtualBox 中的 Ubuntu 26.04（x86-64）；CPU：AMD Ryzen 7 3700X；内核：`7.0.0-38-generic`；`grep -c lam /proc/cpuinfo`：`0`
- clang 版本：`Ubuntu clang version 21.1.8 (6ubuntu1)`
- 编译命令：`clang -fsanitize=hwaddress -O0 -g corpus/controls/positive-uaf.c -o positive-uaf && ./positive-uaf`（实际通过 `bash tools/hwasan-check.sh` 执行，输出路径由脚本指定）
- 结果：编译成功，运行失败：`FATAL: HWAddressSanitizer requires a kernel with tagged address ABI.`，退出码 `99`。x86-64 上 HWASan 依赖 LAM，这台 CPU 没有。
- 备选 A（aarch64 交叉编译 + qemu-user）：QEMU 10.2.1 下普通 ARM64 程序运行成功；HWASan 程序编译成功，但运行报 `Illegal instruction`，首次退出码 `124`；使用 `-cpu max` 重试仍失败，退出码 `137`。当时原因未确定。第二轮在真实 aarch64 上看到同一程序的同一错误，并查明是 GNU ld 的问题（见下文），备选 A 很可能也是这个原因，而不是 QEMU；`tools/hwasan-check.sh` 的备选 A 已改用 lld，未在 QEMU 上重试。

## 第二轮：备选 B，Apple Silicon 上的 aarch64 Linux VM（2026-11-11，记录人：A）

- 主机：Apple M5 Mac，macOS 26.5.1。macOS 本身不行：Apple clang 报 `unsupported option '-fsanitize=hwaddress' for target 'arm64-apple-darwin25.5.0'`。
- 虚拟机：Lima 2.3.0，Apple Virtualization.framework（`--vm-type=vz`，不经过 Docker），Ubuntu 26.04.1 LTS aarch64，内核 `7.0.0-38-generic`（与实验室 VM 同一版本），4 vCPU / 4 GiB；`/proc/sys/abi/tagged_addr_disabled` 为 `0`。
- 工具：`clang=1:21.1.6-71`、`clang-21=1:21.1.8-6ubuntu1`（与实验室 VM 相同），`lld-21=1:21.1.8-6ubuntu1`；系统默认链接器 GNU ld 2.46。
- 问题：用 GNU ld 链接时，`positive-overflow.c` 被检测到，`positive-uaf.c` 却以 SIGILL 退出（`Illegal instruction`，exit 132）。内核日志里的 pc 落在 `main` 中的一条 `0xb2e47fe0`（未定义指令）。HWASan 也给全局变量和字符串常量加标签，取它们的地址时用 `adrp` 加一条 `movk`（重定位 `R_AARCH64_MOVW_PREL_G3`）把标签写进地址高位。GNU ld 按 MOVZ/MOVN 的规则处理这个重定位，值为负（标签 ≥ 0x80）时清掉第 30 位，MOVK 就变成未定义指令。`positive-uaf.c` 的全局变量 `sink` 标签是 `0xdd`，所以中招；标签小于 0x80 的程序不受影响。
- 解决：`-fuse-ld=lld`；`-mllvm -hwasan-globals=0` 关掉全局变量插桩也可以，但会少检查全局变量。用 lld 后两个 positive control 都 DETECTED（exit 99）：`positive-uaf` 报 `tag-mismatch`，`Cause: use-after-free`；`positive-overflow` 报 `Cause: heap-buffer-overflow`。
- 完整 HWASan 列（malloc / arena / freelist × annot 0/1 × 16 case）：positive control 通过，96 个负对照中 94 个 CLEAN；case 12 malloc 的两个对照是 HWASan 自带的 LeakSanitizer 在退出时报泄漏（exit 99），当时被误记为 CLEAN，bug 行本来就是 UNSUPPORTED，不影响结论。harness 已改为对 HWASan 也关掉泄漏检测，并把崩溃的对照记为 TOOL-ERROR，复跑后这两个对照为 CLEAN。各格结果写进每个 case 的 `case.json` `measured` 和 README。这是从工作区跑的开发运行，正式 bundle 待 A5.8/A5.9。
- 正式 bundle（2026-11-13）：`results/2026-11-13-lima-hwasan/`，commit `c214ad3`，同一台 VM（内核已更新到 `7.0.0-43-generic`）。positive control 通过，96 个负对照全部 CLEAN；与 `case.json` 预期比较的 80 格中 79 格一致。不一致的是 case 4 malloc（不标注）：MISSED。这一格的可执行文件在 VM 里重跑 200 次，198 次 DETECTED；标注版那一格 200 次中 199 次 DETECTED。HWASan 的检测是概率性的：检出时的输出是 `tags: b2/08(b2)`，最后一个 granule 是 short granule，影子里存的是有效字节数 8；如果随机给的指针标签恰好也是 8，比较直接通过，这次运行很可能就是这种情况。bundle 保留原样，不为了对上预期而重跑。

## 第三轮：实验室服务器上的 x86-64 别名模式（2026-11-13，记录人：A）

- 机器：实验室服务器 pinwheel12 上的 LXD 容器，Ubuntu 26.04.1 LTS，宿主内核 `6.12.111+deb13-amd64`；CPU：Intel Xeon Gold 6230，`lam: 0`；clang 21.1.8（`1:21.1.8-6ubuntu1`）。
- 默认模式与第一轮相同：`FATAL: HWAddressSanitizer requires a kernel with tagged address ABI.`，exit 99。
- 别名模式：clang 的实验性选项 `-fsanitize-hwaddress-experimental-aliasing`，编译和链接都要加；运行时 `libclang_rt.hwasan_aliases-x86_64` 随 clang 包安装。它不依赖硬件忽略指针高位，而是把同一段堆内存映射到多个虚拟地址，每个标签对应一个别名。两个 positive control 都 DETECTED：`positive-overflow` 报 `tag-mismatch`，`positive-uaf` 报 `tag-mismatch`、`Cause: use-after-free`。
- 完整 HWASan 列（malloc / arena / freelist × annot 0/1 × 16 case）：在 commit `c214ad3` 的副本上，只把 `tools/flags.mk` 的两行 hwasan 选项换成别名模式（不用 lld）。96 个负对照全部 CLEAN。bug 行与第二轮对比（DETECTED / MISSED / UNSUPPORTED）：

  | 分配器 | aarch64 原生（第二轮） | x86-64 别名模式 |
  |---|---|---|
  | malloc | 14 / 1 / 1 | 13 / 1 / 2 |
  | malloc + 标注 | 14 / 1 / 1 | 12 / 1 / 3 |
  | arena | 2 / 12 / 2 | 0 / 14 / 2 |
  | arena + 标注 | 9 / 5 / 2 | 0 / 14 / 2 |
  | freelist | 2 / 14 / 0 | 0 / 16 / 0 |
  | freelist + 标注 | 11 / 5 / 0 | 0 / 16 / 0 |

  malloc 列多出的 UNSUPPORTED 是 case 10、15：别名模式的 malloc 不一定立刻复用刚释放的块，前提条件不成立。
- 原因：用一个小程序看各种大小的 `malloc` 结果。64 B 到 64 KiB 的块在别名区（`0x68…`、`0x69…`），带标签；256 KiB 和 1 MiB 的块由 mmap 分配在别名区之外（`0x7f…`），指针标签为 0，HWASan 对这些地址的读写不做检查。arena 和 freelist 的池都是 1 MiB，所以整个池子不受检查，标注写进影子内存也没有效果。不标注时 case 4（读出池外）和 case 12（池销毁后读）也漏掉，case 12 是读已 munmap 的池，SIGSEGV。
- 指针标签只有 3 位：`__hwasan_tag_pointer(p, 17)` 得到的指针标签是 1，内存标签是 0x11，合法访问也报 `tag-mismatch`。所以即使池子够小，`st_annot.h` 用的 16–255 也不能用。
- 结论：别名模式能在没有 LAM 的 x86-64 上运行，但看不到 64 KiB 以上的池子内部，标注也补不回来，只能测 malloc 和 rewrite 这类每个对象单独 `malloc` 的分配器。它测不出本课题要比较的东西，不纳入检测矩阵；HWASan 仍以第二轮的 aarch64 VM 为准。报告可以把它作为环境限制讨论：在没有 LAM 的 x86-64 上，HWASan 看不到自定义分配器池子的内部。

## 复现

```bash
brew install lima
limactl start --name=seethrough-hwasan --vm-type=vz --cpus=4 --memory=4 --disk=20 \
  --containerd=none --mount-only="$PWD" template:ubuntu-26.04     # 在仓库根目录执行；仓库只读挂载
limactl shell seethrough-hwasan
# 以下在虚拟机内
sudo apt-get update
sudo apt-get install -y clang=1:21.1.6-71 clang-21=1:21.1.8-6ubuntu1 lld-21=1:21.1.8-6ubuntu1 make python3
git clone <挂载的仓库路径> ~/seethrough && cd ~/seethrough      # 挂载只读，结果写在克隆里
python3 harness/run-matrix.py --tools hwasan --allocs malloc arena freelist --annots 0 1 \
  --cases all --out results/<bundle>
```

停机用 `limactl stop seethrough-hwasan`，再用 `limactl start seethrough-hwasan` 继续。

## 标注

HWASan 有公开接口 `<sanitizer/hwasan_interface.h>`：`__hwasan_tag_memory`、`__hwasan_tag_pointer`、`__hwasan_get_tag_from_pointer`。`st_annot.h` 的 `ST_TAG_NEW` / `ST_TAG_POOL` / `ST_POOL_PTR` 用它们给每个对象打新标签，释放时把内存还回池的标签，见 `docs/allocator-annotations.md`。接口只能按 16 字节 granule 打标签，没有 HWASan 自己的 malloc 用的 short granule 形式，所以落在取整空隙里的小越界（case 0-2）标注后仍是 MISSED（C3.5）。

## 环境差异

- 架构不同：aarch64（TBI，8 位标签）对实验室的 x86-64；发行版、内核、clang 版本相同。
- 只用于检测矩阵。主机不同，耗时和 RSS 不能与 VirtualBox VM 上的 ASan / Valgrind 数字对比，所以不做 HWASan 性能实验（C5.4）。
- ASan、Valgrind 的正式结果仍以 x86-64 环境为准。
