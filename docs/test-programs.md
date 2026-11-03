# 测试程序说明（模板）

每个 `corpus/cases/<case>/README.md` 按下面的标题写。报告里的 Test Corpus 一节由这些文件汇总。

```
# <case 名>

## 漏洞
- 类别：heap overflow / underflow / use-after-free / double free
- 访问：read / write
- 一句话：什么对象、在什么时候、被怎样非法访问

## 触发方式
- 分配序列（按 alloc.h 的调用列出，大小、顺序）
- 非法访问在哪一行，偏移多少字节

## 内存布局
- malloc 下：对象之间是什么（malloc header、ASan redzone、对齐填充）
- arena 下：对象紧挨着，中间没有任何东西
- freelist 下：同一 size class，free 后下一次分配拿到同一块
（画一张小图，ASCII 即可）

## 预期结果和理由
| tool | malloc | CMA 未标注 | CMA 标注 | 理由 |
|---|---|---|---|---|
| ASan | DETECTED | MISSED | DETECTED | 越界 1 字节落在 ... |
| Valgrind | ... | ... | ... | |
| HWASan | ... | ... | n/a | 无 CMA 标注接口 |

## 对照组
- `-DST_NEGATIVE_CONTROL` 改了哪一行，为什么分配流量和 bug 版本完全一样
```
