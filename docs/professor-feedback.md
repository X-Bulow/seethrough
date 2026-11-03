# 教授对 Proposal 的反馈

## 原文

> Proposal is accepted.
>
> Note that depending on the CMA, it may be easy to rewrite it to undo the CMA.
>
> The test programs will need to be explained. Please check early if you are able to run HWASAN.

## 翻译

> 提案已通过。
>
> 注意：取决于具体是哪种 CMA，有的 CMA 可能很容易被改写，从而"撤销"掉这个 CMA
> （也就是把它改回直接用 malloc）。
>
> 测试程序需要加以解释说明。请尽早确认你们是否能够运行 HWASan。

## 三点的含义，以及我们怎么回应

### 1. "it may be easy to rewrite it to undo the CMA"

教授在提示一个和 annotation 平行的办法：与其给 CMA 加 ASan / Valgrind 标注，不如直接把 CMA
改掉，让每个对象重新来自 `malloc`，检测能力自然就回来了。对很多 CMA（薄包装、arena 只是
减少 malloc 调用次数）这只是几行改动。这既是威胁（我们的"标注能赢回多少"的问题，可能有一个
更便宜的答案），也是一个实验维度。

我们的回应（任务 B4.x、A5.14）：
- 对我们自己写的 arena / freelist 各做一个 rewrite 版本，记录改动行数；
- 在 rewrite 版本上重跑矩阵，和 annotated 版本、原始版本并列比较；
- 讨论什么时候 rewrite 做不到或者会改变语义：分配器依赖内存布局（相邻对象、header）、
  批量释放（arena reset）、线程局部池、内存上限（memsys5 的固定堆）、性能（malloc 调用次数）；
- 对 SQLite 的 memsys5 / lookaside，rewrite 就是关掉编译选项，这本身就是一个数据点。

### 2. "The test programs will need to be explained"

只给一张 detected / missed 表不够。每个测试程序要说明：它触发什么漏洞、怎么触发、对象在
内存里怎么排布（在 malloc 下和在 CMA 下分别是什么样）、为什么预期某个 tool 能或不能看到、
对照组改了哪一行。

我们的回应（任务 A2.9、docs/test-programs.md）：每个 case 目录带 README.md，按固定模板写，
报告的 Test Corpus 一节直接从这些 README 汇总。

### 3. "Please check early if you are able to run HWASAN"

HWASan 的正式支持平台是 aarch64 Linux（依赖 top-byte-ignore）。我们的实验环境是实验室的
x86-64 Linux 服务器，x86-64 上 HWASan 需要 CPU 和内核支持 LAM（Linear Address Masking），
而且 clang 对 x86-64 HWASan 的支持状态随版本变化，所以教授的担心是实际的：很可能跑不了。

我们的回应（任务 C3.1–C3.5）：Week 1 内在服务器上直接试 `-fsanitize=hwaddress` 编译运行
`corpus/controls/positive-uaf.c`；不行就试 aarch64 交叉编译 + qemu-user，或者组员 Apple Silicon
机器上的 aarch64 Linux VM。结论写进 `docs/hwasan.md`：可行就进矩阵（并说明和其他 tool 的环境
差异），不可行就记录原因并停止投入。
