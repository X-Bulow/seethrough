# 任务清单（一行一个任务，做完打钩）

状态标记：`[ ]` 未开始 `[~]` 进行中 `[x]` 完成 `[-]` 放弃（写明原因）。
每个任务的产出要能在仓库里指出来（文件、CSV、results/ 下的 bundle），否则不算完成。
P0 = 没有它就回答不了 Q1/Q2；P1 = 报告需要；P2 = 时间允许；P3 = stretch。

## 0. 三人共同（Week 1 第一天）

- [x] P0 C0.1 确认统一 allocator 接口 `corpus/include/alloc.h`（A 分支已合入 B 工作分支；malloc / arena 已按新增接口构建验证）
- [x] P0 C0.2 确认 CSV 列和 verdict 五种取值（`harness/README.md`）
- [x] P0 C0.3 确认测试矩阵：tool × allocator × annotation × case × {bug, control}（`harness/run-matrix.py` 按此枚举）
- [x] P0 C0.4 建 Git 远端，三人都能 push；`results/` 只增不改（三人都已推送过分支）
- [x] P0 C0.5 第一条端到端：case00-heap-overflow-write 在 malloc / arena / arena+annot 下各跑一次 ASan，拿到 3 个 verdict（DETECTED / MISSED / DETECTED，见 `results/2026-11-10-ec2-b-core/`）

## A. Test Corpus & Harness（Part A）

### A1 接口与骨架
- [x] P0 A1.1 写 `corpus/include/alloc.h`：`st_alloc / st_free / st_realloc`，由 `-DST_ALLOC=` 选实现
- [x] P0 A1.2 写 `corpus/include/harness.h`：`ST_CASE(n)`、`ST_READY()`、`ST_NEGATIVE_CONTROL` 约定、`st_sink` 防优化
- [x] P0 A1.3 写 `harness/main.c`：调用 case，打印 `ST READY` / `ST DONE` 标记（判 reached / completed 用）

### A2 核心漏洞测试（每个 case：case.c + case.json + README.md；索引见 `corpus/cases/INDEX.md`）
- [x] P0 A2.1 heap overflow：0 越界写 1 字节 / 1 越界读 / 2 写进对齐 slack（偏移 28）/ 3 远距离写进第三个活对象（偏移 64）/ 4 读出 pool 之外
- [x] P0 A2.2 heap underflow：5 越界写前 1 字节 / 6 越界读 / 7 覆写 header 所在的 8 字节
- [x] P0 A2.3 use after free：8 写 / 9 读 / 10 重用后写（标注的天花板）/ 11 realloc 搬走后读 / 12 整个 pool 销毁后读
- [x] P0 A2.4 free 类错误：13 double free / 14 释放内部指针 / 15 重用后 double free
- [x] P0 A2.5 每个 case 的 negative control：分配/释放流量逐字节相同，只替换非法访问那一行（13 的两个 image 都是 2 次 free）
- [x] P0 A2.6 前置条件机制：case 10/11/15 打印 marker，`case.json` 的 `requires` 让条件不满足的行记 UNSUPPORTED 而不是 MISSED
- [x] P0 A2.7 `st_alloc_pool_bytes()` 加进 `alloc.h`（case 4 要定位 pool 边界）；`st_alloc_fini()` 要求幂等（case 12）
- [x] P0 A2.8 每个 case 的 README：触发方式、内存布局图、预期每个 tool 的结果及理由（教授要求）
- [x] P1 A2.9 在服务器上跑完 16 个 case 并把 `measured` 填回每个 `case.json`，注明 bundle（2026-11-13：ASan / Valgrind 来自实验室服务器的四个 bundle，HWASan 来自 `results/2026-11-13-lima-hwasan/`；case 03 Valgrind malloc、case 04 ASan 四个池列的预期按实测改正并写明原因，每个 case 的 README 加了正式结果表）
- [x] P0 A2.10 合入 B1.2/B1.3 后重推预期：case 7、8、9、11、13、14 按新 arena（side table、会搬迁的 realloc）和 free list 改了 ASan/Valgrind/HWASan 预期；2026-11-07 本机冒烟（asan + none × malloc/arena/freelist）与 ASan 预期 80 格全部一致，新旧两次冒烟都留在 `measured`。Valgrind 格仍是预测，等 A2.9

### A3 控制组
- [x] P0 A3.1 positive control：malloc 的 UAF，ASan/Valgrind/HWASan 必须报；不报则本轮 exit 75 无 verdict（`corpus/controls/positive-uaf.c`）
- [x] P0 A3.2 positive control：malloc 的 1 字节 heap overflow（`corpus/controls/positive-overflow.c`）
- [x] P1 A3.3 bug-free 对照程序：一组完全没有漏洞的程序，确认各 tool 在 CMA 下不误报（由 A2.5 的 16 个 negative control 承担；EC2 core bundle 192 个对照全部 CLEAN，无 FALSE-POSITIVE）

### A4 自动化
- [x] P0 A4.1 `harness/run-matrix.py`：枚举矩阵、编译、运行、超时、收集 stdout/stderr/exit code
- [x] P0 A4.2 `harness/classify.py`：从 tool 输出判 DETECTED / MISSED / FALSE-POSITIVE / UNSUPPORTED / TOOL-ERROR
- [x] P0 A4.3 CSV 输出：`results/<date>-<arm>/matrix.csv`，列见 `harness/README.md`
- [x] P0 A4.4 每个 bundle 带 `env.txt`：tool 版本、编译器版本、flags、服务器 CPU / 内核（`tools/env.sh` 生成）
- [x] P1 A4.5 `harness/render-matrix.py`：CSV → 报告用 Detection Matrix（markdown / LaTeX 表）；`--check` 对照 `case.json` 的预期

### A5 检测实验（每一行就是矩阵里的一个 cell 组，A 跑，B/C 提供 allocator / tool）
正式结果（2026-11-13）：ASan、Valgrind 来自实验室服务器（x86-64，commit `6b54739`）的 `results/2026-11-13-lab-{core,memsys5,lookaside,rewrite}/`；HWASan 来自 Mac 上 aarch64 Lima VM 的 `results/2026-11-13-lima-hwasan/`（commit `c214ad3`），实验室服务器的 CPU 没有 LAM，x86-64 别名模式又看不到池子内部（`docs/hwasan.md` 第三轮）。B 在 AWS EC2 上跑的 bundle（commit `2763402`）与实验室结果 352 个 bug 格逐格一致，作为另一台机器上的复现；其 `env.txt` 里的 `dirty=1..5` 是旧版 `tools/env.sh` 把本轮尚未提交的结果目录也算进去了，工作区本身是干净的。
- [x] P0 A5.1 malloc 下用 ASan 检测 7 类（`results/2026-11-13-lab-core/`）
- [x] P0 A5.2 arena CMA 下用 ASan 检测 7 类（未标注）（同上）
- [x] P0 A5.3 arena CMA + ASan manual poisoning 下检测 7 类（同上）
- [x] P0 A5.4 freelist CMA 下用 ASan 检测 7 类（未标注 / 标注）（同上）
- [x] P0 A5.5 malloc 下用 Valgrind Memcheck 检测 7 类（同上）
- [x] P0 A5.6 arena / freelist CMA 下用 Valgrind 检测 7 类（未标注）（同上）
- [x] P0 A5.7 arena / freelist CMA + Valgrind mempool 标注下检测 7 类（同上）
- [x] P0 A5.8 malloc 下用 HWASan 检测 7 类（在 Mac 上的 aarch64 VM 中运行，见 `docs/hwasan.md`；`results/2026-11-13-lima-hwasan/`）
- [x] P0 A5.9 arena / freelist CMA 下用 HWASan 检测 7 类（标注用 `hwasan_interface.h` 的打标签接口，即 `st_annot.h` 的 `ST_TAG_*`；同上）
- [ ] P1 A5.10 UBSan（`-fsanitize=bounds,object-size`）在 malloc / CMA 下检测 7 类
- [x] P1 A5.11 memsys5 / lookaside 下用 ASan、Valgrind 检测 7 类（依赖 B3）（`results/2026-11-13-lab-memsys5/`、`results/2026-11-13-lab-lookaside/`）
- [ ] P1 A5.12 使用 C4 已验证的 Ubuntu 18.04 Docker / LowFat clang 4.0.0 环境检测 7 类；记录填充空间内越界、跨分配边界越界及 UAF 的实际结果，并注明容器环境差异（运行步骤见 `docs/lowfat.md`）
- [x] P1 A5.13 复查所有 MISSED / FALSE-POSITIVE，确认不是编译配置、优化或 harness 的问题（2026-11-14：174 个 MISSED、0 个 FALSE-POSITIVE，全部执行到缺陷行且工具无任何报告，归入 7 类机制；`harness/audit-missed.py` 可重跑，结论见 `docs/missed-review.md`）
- [x] P1 A5.14 CMA-rewrite 版本（B4）下重跑 ASan / Valgrind，和标注版本对比（`results/2026-11-13-lab-rewrite/`，对比见 `docs/cma-rewrite.md`）

### A6 Week 2 扩展
- [x] P1 A6.1 读/写变体补全（每类 read + write 各一）（overflow 0/1、underflow 5/6、UAF 8/9；free 类错误没有读写之分）
- [ ] P2 A6.2 overflow 距离变体：1 字节 / padding 内 / size-class slack 内（stretch (a)）
- [x] P1 A6.3 完整 Detection Matrix 和文字解释（报告 §5，表 4–7、图 2；表格由 `report/scripts/gen.py` 从正式 bundle 生成）
- [x] P1 A6.4 报告章节：Test Corpus、Methodology、Q1 Results（`report/src/04-methodology.tex`、`05-detection.tex`）

### A7 真实 SQLite 漏洞（Tier 2，验证 Tier 1 的结论能否迁移；Week 2 末–Week 3）
- [x] P1 A7.1 `tools/fetch-sqlite.sh 3.22.0`：pin 与 capstone engine-repros 一致（sqlite3.c sha256 7991acd0…），源码只进 `vendor/`
- [x] P1 A7.2 从 capstone `bug-corpora/sqlite/engine-repros` 移植 4 个 case（03、19 temporal；29、31 spatial）到 `corpus/real/`，case.c 原样，PROVENANCE 带 sha256
- [x] P1 A7.3 三个 arm 的构建：memsys5（SQLITE_CONFIG_HEAP，lookaside 关）/ default（SQLite 出厂配置）/ rewrite（无 memsys5，LOOKASIDE=0,0，PCACHE_INITSZ=0）；`make real`，引擎按 (tool, arm, group) 缓存
- [x] P1 A7.4 gate：rewrite arm 下 ASan 必须报出该 bug，否则该 case 其余行 UNSUPPORTED；每个 case 自己的可达性标记缺失则 TOOL-ERROR（`harness/run-real.py`）
- [x] P1 A7.5 服务器上跑 asan / valgrind × 三个 arm（2026-11-16，`results/2026-11-16-lab-real/real.csv`，commit 2098f2a；LowFat 不在范围内）；结果写进 `corpus/real/README.md` 和各 case 的 `case.json` / README
- [x] P1 A7.6 classify 的 SEGV 规则（sanitizer 信号处理函数的报告记 MISSED crashed）在服务器上用 case 19 memsys5 arm 复核（2026-11-16 确认；同一次崩溃在 Memcheck 下是 0x2 处的 Invalid read，harness 记 DETECTED，报告里按漏报解读）
- [ ] P2 A7.7 越界步长：29/31 的 fuzz 镜像越界约 2 KB，越过整个 arena 和 pcache bulk 块；找或构造一个越界停在 arena 内的真实 spatial case（配合 A6.2 stretch (a)）
- [ ] P2 A7.8 PostgreSQL mmgr（capstone `postgres/mmgr-repros`）或 CPython pymalloc 各取 1 个 case，时间不够就砍
- [x] P1 A7.9 报告段落（§7.3，2026-11-16 按 A7.5 实验室正式结果重写）：Tier 1 的 MISSED 在真实程序里是否重现（temporal 是，spatial 取决于步长）；SQLite 不化简的理由；default arm 两层的说明

## B. CMA & Annotations（Part B）

- [x] P0 B1.1 实现 `allocators/malloc/`：直接转发 malloc（基线）
- [x] P0 B1.2 实现 `allocators/arena/`：bump-pointer arena，一次 malloc 大块，free 不归还；side table 记录大小和存活状态，`realloc` 搬迁，`fini` 可重复调用
- [x] P0 B1.3 实现 `allocators/freelist/`：固定 size-class free list，free 立即重用
- [x] P0 B2.1 ASan manual poisoning：`ASAN_POISON_MEMORY_REGION` / `UNPOISON`，`-DST_ANNOT=1` 时启用；Arena / Free list 本机开发验证通过
- [x] P0 B2.2 Valgrind mempool：`VALGRIND_CREATE_MEMPOOL` / `MEMPOOL_ALLOC` / `MEMPOOL_FREE`；Arena / Free list 在 Linux 开发容器和 EC2 x86-64 正式矩阵均验证通过
- [x] P1 B2.3 记录每个 allocator 标注了哪些边界，哪些标注不了（`docs/allocator-annotations.md`）
- [x] P1 B3.1 SQLite memsys5 作为 `allocators/sqlite/`（`SQLITE_ENABLE_MEMSYS5`，`sqlite3_malloc64` 走它）；另有 ASan/Valgrind 标注补丁，3.53.3 全 16 case 已在 EC2 x86-64 正式验证，64 个负例 CLEAN
- [x] P2 B3.2 SQLite lookaside 作为另一层；验证命中 lookaside slot 且释放后立即重用，ASan/Valgrind 全 16 case 已在 EC2 x86-64 正式验证，32 个负例 CLEAN
- [x] P0 B4.1 CMA rewrite：arena / freelist 改写成直接 malloc/free，两份实现各 14 行（见各自 README）
- [x] P1 B4.2 分析 rewrite 的可行性边界：见 `docs/cma-rewrite.md`
- [x] P1 B4.3 Rewrite vs Annotation 对比：EC2 Ubuntu 26.04 x86-64 上完整 ASan/Valgrind 16-case 矩阵、全部负对照、五次重复性能与 RSS 已完成；原始 bundle 见 `results/README.md`，解释见 `docs/cma-rewrite.md`
- [x] P1 B5.1 报告章节：`report/part-b.md` 已写入 CMA Implementation、Annotations、CMA Rewrite、Q1 Analysis 和 EC2 正式结果；C 的 VirtualBox 性能结果单独标注

## C. Tools & Performance（Part C）

### C1 工具环境（实验室 x86-64 Linux VM；ASan / UBSan / Valgrind 原生运行，LowFat 使用 Ubuntu 18.04 Docker）
- [x] P0 C1.1 `tools/setup-server.sh`：在服务器上装或源码构建固定版本的 clang（ASan/UBSan/HWASan）、valgrind；记录版本
- [x] P0 C1.2 `tools/env.sh`：打印 CPU 型号、内核版本、clang / gcc / valgrind 版本、flags，写进每个 results bundle 的 `env.txt`
- [x] P0 C1.3 `tools/flags.mk`：每个 tool 的 CFLAGS / LDFLAGS / 环境变量（`ASAN_OPTIONS` 等）
- [x] P0 C1.4 `docs/environment.md`：填表（服务器 CPU、内核、工具版本）
- [~] P0 C1.5 确认三人可登录各自实验 VM、通过 Git 同步同一远程仓库、各自的 `results/` 目录可写（复现步骤已上传，见 [docs/reproducibility.md](docs/reproducibility.md)；C 已确认登录、Git 同步及结果写入；A/B 待按步骤确认）

### C3 HWASan（Week 1 必须出结论；x86-64 上是真问题）
- [x] P0 C3.1 查服务器 CPU 是否支持 LAM（Linear Address Masking，`grep lam /proc/cpuinfo`）、内核是否 ≥ 6.2 并启用 LAM；clang 版本是否支持 `-fsanitize=hwaddress` 在 x86_64
- [x] P0 C3.2 直接试：`clang -fsanitize=hwaddress corpus/controls/positive-uaf.c`，运行，看是否 DETECTED；把输出粘进 `docs/hwasan.md`
- [x] P0 C3.3 若原生不行，试备选 A：aarch64 交叉编译 + `qemu-aarch64` 用户态运行（HWASan 的 TBI 在 qemu-user 下可用）；备选 B：组员的 Apple Silicon 机器上的 aarch64 Linux VM（2026-11-11 备选 B 在 Apple M5 的 Lima VM 中跑通，需用 lld 链接）
- [x] P0 C3.4 结论写进 `docs/hwasan.md`：可行（哪种方式）→ 纳入矩阵，并说明该方式和其他 tool 的环境差异；不可行 → 写明错误和原因，不再投入（2026-11-11 更新：可行，方式为备选 B）
- [x] P1 C3.5 若可行：HWASan 的 tag 粒度（16 字节）对 1 字节 overflow 的影响，设计 case 时要让越界跨 granule（malloc 靠 short granule 抓到；分配器标注只能按整 granule 打标签，case 0-2 标注后仍 MISSED）

### C4 LowFat（Ubuntu 18.04 Docker 容器中构建并验证）
- [x] P1 C4.1 在 Ubuntu 18.04 Docker 容器内构建固定 commit 的 LowFat clang，记录环境、构建和运行指令（clang 4.0.0 构建及自带测试通过，见 `docs/lowfat.md`）
- [x] P1 C4.2 验证 LowFat 的检测范围：运行 `corpus/controls/` 及安全 / 跨分配边界写入测试，记录输出和退出码（原有 1 字节 overflow 和 UAF 未检测；安全访问正常，跨分配边界写入报警，exit 134，见 `docs/lowfat.md`）

### C5 Q2 性能
- [x] P0 C5.1 SQLite speedtest1：baseline -O2，ASan，Valgrind；5 次取中位数，wall time + peak RSS
- [x] P0 C5.2 同上加 SQLite 自带 memsys5 开关，看 CMA 对 overhead 的影响
- [~] P1 C5.3 annotated vs unannotated 的 overhead（配合 B2）：B 已交付 EC2 五次重复的 90 行原始 CSV、汇总与报告解释，见 `results/2026-11-10-allocator-churn-IkUTIU/`；C 仍需在其 Q2 章节接入并标注与 VirtualBox 数据的机器差异
- [ ] P1 C5.4 HWASan overhead（若 C3 可行）
- [x] P2 C5.5 PostgreSQL regression 子集 或 Lua / CPython benchmark
- [x] P1 C5.6 `benchmarks/plot.py`：CSV → 性能图
- [~] P1 C5.7 报告章节：Tool Setup、Performance Methodology、Q2 Results（A 写了初稿 `report/src/06-performance.tex`，待 C 审阅）

## D. 报告与提交（Week 2–3，三人）

- [x] P0 D1 Introduction、Related Work（CMASan、MSET、Jung CGO'25）（初稿，`report/src/01-*`、`03-*`）
- [x] P0 D2 回应教授三点：CMA rewrite、测试程序解释、HWASan 结论（报告 §7.2）
- [x] P0 D3 Discussion / Limitations / Conclusion（初稿，`report/src/07-*`、`08-*`）
- [~] P0 D4 复现检查：在服务器上从干净 clone 跑 `tools/setup-server.sh` + `harness/run-matrix.py` 重新生成 Detection Matrix 和性能图（C 部分已复现，见 `docs/reproducibility.md`；Detection Matrix 待完成）
- [~] P0 D5 15 页报告定稿，11 月 19 日前提交（2026-11-14 初稿 15 页：`make -C report`；2026-11-16 填组号 501、缩短标题、补全 A 负责的 §4.1 / §4.3 / §5、§7.3 换成 A7.5 正式结果，17 页；待填视频链接、三人审阅）
- [ ] P1 D6 演示视频（如果课程要求）
