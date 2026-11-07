# 9 use-after-free-read — 释放后读，中间没有任何分配

## 漏洞
- 类别：use after free　访问：read
- 对象：`a`，24 字节，释放后再读
- 一句话：`st_free(a)` 之后 `st_sink(a[0])`

## 触发方式
与 case 8 相同，访问换成读；对照组把读移到 free 之前。

## 为什么它是最安静的一类缺陷
一次 stale read 什么都不破坏，所以后面不会有任何崩溃指向它。在未标注的 arena 下 `st_free` 不回收任何东西，它读回的就是对象自己的旧内容（0x5a），程序察觉不到，只看 malloc 生命周期的 tool 也察觉不到。

真实世界里这一类占绝大多数：capstone 的 SQLite engine 语料里 27 个计入的 case 有 19 个是 temporal，其中大部分是 stale read（见 `corpus/real/README.md`）。

## 预期结果
同 case 8（见 `case.json`）：B1.2 之后 arena 用 side table 记下对象大小，已标注 arena 在 free 时 re-poison，能检出；未标注的 arena 和 free list 仍然漏报。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | MISSED |
| none | MISSED | MISSED | MISSED |

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | **DETECTED use-after-poison** | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

加粗的格子与 2026-11-05 那次不同，原因同 case 8。
