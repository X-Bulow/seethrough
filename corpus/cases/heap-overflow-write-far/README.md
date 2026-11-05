# 3 heap-overflow-write-far — 越界 40 字节，跨过邻居写进第三个活对象

## 漏洞
- 类别：heap overflow　访问：write
- 对象：`a`，24 字节，连续三次 `st_alloc(24)` 中的第一个
- 一句话：写 `a[64]`。在 16 字节对齐的 arena 里 a=[0,32) b=[32,64) c=[64,96)，所以 `a[64]` 就是 `c[0]`

## 这个 case 是全套里最重要的几行之一
它说明**标注对空间类漏洞也有天花板**：

> `a[64]` 落在 `c[0]`。c 是活对象，必须是 unpoisoned 的，否则 c 自己的访问就会误报。所以任何"分配时 poison 空隙"的方案都对这一行无效。

对比 case 0：那里越界落在 a 自己的对齐 slack 里，标注能救回来。两个 case 的差别只有偏移量，结论却相反。报告里应该把 case 0 / 2 / 3 当成一组距离序列来讲（完整的距离扫描是 A6.2）。

在 malloc 下这一行还顺便测 redzone 的**宽度**：如果偏移 64 跨过了 a 的右 redzone 落进 b 的数据，ASan 也看不见。

## 内存布局
```
arena:   [ a: 24 |slack][ b: 24 |slack][ c: 24 |slack]
         0      24   32  32     56  64  64          96
                              a[64] ────────────────┘ = c[0]，活字节

malloc + ASan:  [rz][ a: 24 ][rz ≥16][rz][ b ]...
                a[64] 可能跨过 a 的右 redzone 落进 b 的数据 → 不报
```

## 预期结果
见 `case.json`。LowFat 在这一行**反而报**（malloc 下偏移 64 超出了 32 字节 size class），和 case 1、case 2 正好相反 —— 这组对比是 LowFat 那一节的主要内容。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | **MISSED** | MISSED | **MISSED** |
| none | MISSED | MISSED | MISSED |

malloc 下 ASan 漏报已经在本机复现（预测时标的是 to verify），服务器上要再确认一次 Linux 的 ASan redzone 宽度是否相同。已标注 arena 下的漏报是设计使然，不是 bug。
