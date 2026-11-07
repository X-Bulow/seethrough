# 0 heap-overflow-write — 越界写 1 字节

## 漏洞
- 类别：heap overflow　访问：write
- 对象：`a`，请求 24 字节，是连续两次 `st_alloc(24)` 中的第一个
- 一句话：写 `a[24]`，越过请求末尾 1 字节

## 触发方式
```
a = st_alloc(24);  b = st_alloc(24);
memset(a, 0x5a, 24);  memset(b, 0x5a, 24);
ST_READY();
a[24] = 1;              // 缺陷
```
对照组把这一行换成 `a[23] = 1`（最后一个合法字节），分配与释放完全相同。

## 内存布局
```
malloc + ASan:   [左 redzone ≥16][ a: 24 ][右 redzone ≥16] ... [左 redzone][ b: 24 ]...
                 a[24] 落在右 redzone，shadow 标记不可寻址 → 报

arena (16 对齐):  [ a: 24 | slack 8 ][ b: 24 | slack 8 ][ ... ]
                 偏移:    0      24  32            56  64
                 a[24] 落在 a 自己的对齐 slack（24..31），不是 b 的数据
                 未标注：整块 arena 都是 ASan 眼里的一个活对象 → 不报
                 已标注：arena 分配时只 unpoison 24 字节，24..31 仍 poisoned → 报
```
**这一行能被标注救回来，靠的是对齐 slack。** 如果越界正好落到 `b[0]`（偏移 32），那是一个活对象的字节，必须 unpoison，标注就无能为力 —— 那是 case 3 测的事。

## 预期结果
见 `case.json` 的 `expected`。要点：
- ASan 记住的是**请求大小**，所以偏移 24 在 malloc 和已标注 arena 下都报
- LowFat 的边界是**size class**（24 → 32），偏移 24 在界内，连 malloc 都不报。这是 LowFat 已知的 sub-object 精度问题，不是 CMA 造成的；对比 case 3
- UBSan 需要静态数组边界，分配器返回的指针没有 → 全列不报

## 本机冒烟（2026-11-05，macOS arm64，Apple clang 21，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED **use-after-poison** |
| none | MISSED | MISSED | MISSED |

注意已标注 arena 下 ASan 报的是 `use-after-poison` 而不是 `heap-buffer-overflow`：verdict 相同，报告**种类**不同。报告里的表格和任何按关键字统计的脚本都要知道这件事。

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

free list 两列和 arena 两列结论相同。
