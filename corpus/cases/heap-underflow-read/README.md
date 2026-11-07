# 6 heap-underflow-read — 越界读前 1 字节

## 漏洞
- 类别：heap underflow　访问：read
- 对象：`a`，24 字节，在另一个 24 字节对象 `first` 之后分配
- 一句话：读 `*(a - 1)`

## 触发方式
与 case 5 相同的分配序列，缺陷行换成 `st_sink(*(a - 1))`；对照组读 `a[0]`。

读为什么单独成案见 case 1 的说明；两侧为什么不对称见 case 5 的说明。

## 内存布局
同 case 5：`*(a-1)` 是 `first` 的最后一个对齐 slack 字节。

## 预期结果
同 case 5（见 `case.json`）。

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
