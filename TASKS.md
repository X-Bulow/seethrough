# 任务清单（一行一个任务，做完打钩）

状态标记：`[ ]` 未开始 `[~]` 进行中 `[x]` 完成 `[-]` 放弃（写明原因）。
每个任务的产出要能在仓库里指出来（文件、CSV、results/ 下的 bundle），否则不算完成。
P0 = 没有它就回答不了 Q1/Q2；P1 = 报告需要；P2 = 时间允许；P3 = stretch。

## 0. 三人共同（Week 1 第一天）

- [ ] P0 C0.1 确认统一 allocator 接口 `corpus/include/alloc.h`（A 起草，B 确认可以实现）
- [ ] P0 C0.2 确认 CSV 列和 verdict 五种取值（`harness/README.md`）
- [ ] P0 C0.3 确认测试矩阵：tool × allocator × annotation × case × {bug, control}
- [ ] P0 C0.4 建 Git 远端，三人都能 push；`results/` 只增不改
- [ ] P0 C0.5 第一条端到端：heap-overflow-write 在 malloc / arena / arena+annot 下各跑一次 ASan，拿到 3 个 verdict

## A. Test Corpus & Harness（Part A）

### A1 接口与骨架
- [ ] P0 A1.1 写 `corpus/include/alloc.h`：`st_alloc / st_free / st_realloc`，由 `-DST_ALLOC=` 选实现
- [ ] P0 A1.2 写 `corpus/include/harness.h`：`ST_CASE(n)`、`ST_READY()`、`ST_NEGATIVE_CONTROL` 约定、`st_sink` 防优化
- [ ] P0 A1.3 写 `harness/main.c`：调用 case，打印 `ST READY` / `ST DONE` 标记（判 reached / completed 用）

### A2 核心漏洞测试（每个 case：case.c + case.json + README.md）
- [ ] P0 A2.1 heap-overflow-write（1 字节越界写）
- [ ] P0 A2.2 heap-overflow-read
- [ ] P0 A2.3 heap-underflow-write
- [ ] P0 A2.4 heap-underflow-read
- [ ] P0 A2.5 use-after-free-write
- [ ] P0 A2.6 use-after-free-read
- [ ] P0 A2.7 double-free
- [ ] P0 A2.8 每个 case 的 negative control：分配/释放流量逐字节相同，只替换非法访问那一行
- [ ] P0 A2.9 每个 case 的 README：触发方式、内存布局图、预期每个 tool 的结果及理由（教授要求）

### A3 控制组
- [ ] P0 A3.1 positive control：malloc 的 UAF，ASan/Valgrind/HWASan 必须报；不报则本轮 exit 75 无 verdict
- [ ] P0 A3.2 positive control：malloc 的 1 字节 heap overflow
- [ ] P1 A3.3 bug-free 对照程序：一组完全没有漏洞的程序，确认各 tool 在 CMA 下不误报

### A4 自动化
- [ ] P0 A4.1 `harness/run-matrix.py`：枚举矩阵、编译、运行、超时、收集 stdout/stderr/exit code
- [ ] P0 A4.2 `harness/classify.py`：从 tool 输出判 DETECTED / MISSED / FALSE-POSITIVE / UNSUPPORTED / TOOL-ERROR
- [ ] P0 A4.3 CSV 输出：`results/<date>-<arm>/matrix.csv`，列见 `harness/README.md`
- [ ] P0 A4.4 每个 bundle 带 `env.txt`：tool 版本、编译器版本、flags、服务器 CPU / 内核（`tools/env.sh` 生成）
- [ ] P1 A4.5 `harness/render-matrix.py`：CSV → 报告用 Detection Matrix（markdown / LaTeX 表）

### A5 检测实验（每一行就是矩阵里的一个 cell 组，A 跑，B/C 提供 allocator / tool）
- [ ] P0 A5.1 malloc 下用 ASan 检测 7 类
- [ ] P0 A5.2 arena CMA 下用 ASan 检测 7 类（未标注）
- [ ] P0 A5.3 arena CMA + ASan manual poisoning 下检测 7 类
- [ ] P0 A5.4 freelist CMA 下用 ASan 检测 7 类（未标注 / 标注）
- [ ] P0 A5.5 malloc 下用 Valgrind Memcheck 检测 7 类
- [ ] P0 A5.6 arena / freelist CMA 下用 Valgrind 检测 7 类（未标注）
- [ ] P0 A5.7 arena / freelist CMA + Valgrind mempool 标注下检测 7 类
- [ ] P0 A5.8 malloc 下用 HWASan 检测 7 类（前提 C3.1 可行）
- [ ] P0 A5.9 arena / freelist CMA 下用 HWASan 检测 7 类（HWASan 没有官方 CMA 标注接口，记录这一点）
- [ ] P1 A5.10 UBSan（`-fsanitize=bounds,object-size`）在 malloc / CMA 下检测 7 类
- [ ] P1 A5.11 memsys5 / lookaside 下用 ASan、Valgrind 检测 7 类（依赖 B3）
- [ ] P1 A5.12 LowFat 在实验室 x86-64 服务器上检测 7 类（依赖 C4；服务器是原生 x86-64，LowFat 可行性比原计划高）
- [ ] P1 A5.13 复查所有 MISSED / FALSE-POSITIVE，确认不是编译配置、优化或 harness 的问题
- [ ] P1 A5.14 CMA-rewrite 版本（B4）下重跑 ASan / Valgrind，和标注版本对比

### A6 Week 2 扩展
- [ ] P1 A6.1 读/写变体补全（每类 read + write 各一）
- [ ] P2 A6.2 overflow 距离变体：1 字节 / padding 内 / size-class slack 内（stretch (a)）
- [ ] P1 A6.3 完整 Detection Matrix 和文字解释
- [ ] P1 A6.4 报告章节：Test Corpus、Methodology、Q1 Results

## B. CMA & Annotations（Part B）

- [ ] P0 B1.1 实现 `allocators/malloc/`：直接转发 malloc（基线）
- [ ] P0 B1.2 实现 `allocators/arena/`：bump-pointer arena，一次 malloc 大块，free 不归还
- [ ] P0 B1.3 实现 `allocators/freelist/`：固定 size-class free list，free 立即重用
- [ ] P0 B2.1 ASan manual poisoning：`ASAN_POISON_MEMORY_REGION` / `UNPOISON`，`-DST_ANNOT=1` 时启用
- [ ] P0 B2.2 Valgrind mempool：`VALGRIND_CREATE_MEMPOOL` / `MEMPOOL_ALLOC` / `MEMPOOL_FREE`
- [ ] P1 B2.3 记录每个 allocator 标注了哪些边界，哪些标注不了（如 freelist 重用后的 UAF）
- [ ] P1 B3.1 SQLite memsys5 作为 `allocators/sqlite/`（`SQLITE_ENABLE_MEMSYS5`，`sqlite3_malloc` 走它）
- [ ] P2 B3.2 SQLite lookaside 作为另一层
- [ ] P0 B4.1 CMA rewrite：把 arena / freelist 改写成直接 malloc/free（教授提示的 "undo the CMA"），记录改了几行
- [ ] P1 B4.2 分析 rewrite 的可行性边界：哪些 CMA 容易撤销（薄包装），哪些不能（依赖布局、批量释放、线程局部池）
- [ ] P1 B4.3 Rewrite vs Annotation 对比：检测能力、语义变化、性能（配合 C）
- [ ] P1 B5.1 报告章节：CMA Implementation、Annotations、CMA Rewrite、Q1 Analysis

## C. Tools & Performance（Part C）

### C1 工具环境（实验室 x86-64 Linux 服务器，原生运行，不用 Docker）
- [x] P0 C1.1 `tools/setup-server.sh`：在服务器上装或源码构建固定版本的 clang（ASan/UBSan/HWASan）、valgrind；记录版本
- [x] P0 C1.2 `tools/env.sh`：打印 CPU 型号、内核版本、clang / gcc / valgrind 版本、flags，写进每个 results bundle 的 `env.txt`
- [x] P0 C1.3 `tools/flags.mk`：每个 tool 的 CFLAGS / LDFLAGS / 环境变量（`ASAN_OPTIONS` 等）
- [x] P0 C1.4 `docs/environment.md`：填表（服务器 CPU、内核、工具版本）
- [ ] P0 C1.5 确认三人都能登录服务器、共享同一份 clone、`results/` 目录可写

### C3 HWASan（Week 1 必须出结论；x86-64 上是真问题）
- [x] P0 C3.1 查服务器 CPU 是否支持 LAM（Linear Address Masking，`grep lam /proc/cpuinfo`）、内核是否 ≥ 6.2 并启用 LAM；clang 版本是否支持 `-fsanitize=hwaddress` 在 x86_64
- [x] P0 C3.2 直接试：`clang -fsanitize=hwaddress corpus/controls/positive-uaf.c`，运行，看是否 DETECTED；把输出粘进 `docs/hwasan.md`
- [x] P0 C3.3 若原生不行，试备选 A：aarch64 交叉编译 + `qemu-aarch64` 用户态运行（HWASan 的 TBI 在 qemu-user 下可用）；备选 B：组员的 Apple Silicon 机器上的 aarch64 Linux VM
- [x] P0 C3.4 结论写进 `docs/hwasan.md`：可行（哪种方式）→ 纳入矩阵，并说明该方式和其他 tool 的环境差异；不可行 → 写明错误和原因，不再投入
- [ ] P1 C3.5 若可行：HWASan 的 tag 粒度（16 字节）对 1 字节 overflow 的影响，设计 case 时要让越界跨 granule

### C4 LowFat（本轮构建配置检查失败，降为 P2）
- [-] P2 C4.1 在服务器上构建 LowFat clang（https://github.com/GJDuck/LowFat），记录 commit 和构建命令（原版构建在 joinid 偏移检查失败，见 `docs/lowfat.md`；本轮不再投入）
- [-] P2 C4.2 跑 `corpus/controls/`；不行就记录错误，降回 P2 不再投入（未生成可用编译器，无法运行 controls）

### C5 Q2 性能
- [x] P0 C5.1 SQLite speedtest1：baseline -O2，ASan，Valgrind；5 次取中位数，wall time + peak RSS
- [x] P0 C5.2 同上加 SQLite 自带 memsys5 开关，看 CMA 对 overhead 的影响
- [ ] P1 C5.3 annotated vs unannotated 的 overhead（配合 B2）
- [ ] P1 C5.4 HWASan overhead（若 C3 可行）
- [ ] P2 C5.5 PostgreSQL regression 子集 或 Lua / CPython benchmark
- [x] P1 C5.6 `benchmarks/plot.py`：CSV → 性能图
- [ ] P1 C5.7 报告章节：Tool Setup、Performance Methodology、Q2 Results

## D. 报告与提交（Week 2–3，三人）

- [ ] P0 D1 Introduction、Related Work（CMASan、MSET、Jung CGO'25）
- [ ] P0 D2 回应教授三点：CMA rewrite、测试程序解释、HWASan 结论
- [ ] P0 D3 Discussion / Limitations / Conclusion
- [~] P0 D4 复现检查：在服务器上从干净 clone 跑 `tools/setup-server.sh` + `harness/run-matrix.py` 重新生成 Detection Matrix 和性能图（C 部分已复现，见 `docs/reproducibility.md`；Detection Matrix 待完成）
- [ ] P0 D5 15 页报告定稿，11 月 19 日前提交
- [ ] P1 D6 演示视频（如果课程要求）
