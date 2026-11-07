# 1 heap-overflow-read — 越界读 1 字节

## 漏洞
- 类别：heap overflow　访问：read
- 对象：`a`，24 字节，连续两次 `st_alloc(24)` 中的第一个
- 一句话：读 `a[24]`，越过请求末尾 1 字节

## 触发方式
与 case 0 相同的分配序列，缺陷行是 `st_sink(a[24])`；对照组读 `a[23]`。

## 为什么读要单独成一个 case
`corpus/README.md` 规则 4：读和写分开。理由不是形式主义：
- 一次越界**读**什么都不破坏，所以后续永远不会因为它崩溃，没有"迟到的证据"
- Valgrind 只在字节**不可寻址**时报 invalid read；在 arena 内部每个字节都是可寻址的
- ASan 对读和写是两套 instrumentation，可以一个插桩一个漏

在 arena 下这次读还会返回一个"合理"的值（`b[0]` 是 0x5a），程序自己也察觉不到。

## 内存布局
同 case 0：`a[24]` 落在 a 的 16 字节对齐 slack 内（24..31），不是 b 的数据。

## 预期结果
同 case 0（见 `case.json`）。LowFat 在 malloc 下也不报，因为 24 在 32 字节 size class 之内。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED |

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

free list 两列和 arena 两列结论相同。
