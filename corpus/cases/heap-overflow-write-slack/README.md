# 2 heap-overflow-write-slack — 写进分配器自己的对齐 slack

## 漏洞
- 类别：heap overflow　访问：write
- 对象：`a`，请求 24 字节，任何 16 字节对齐的分配器都会占 32 字节
- 一句话：写 `a[28]`，越过**请求**末尾 4 字节，但仍在分配器**交出的块**之内

## 为什么这个 case 和 case 0 不同
24 字节的请求被 round 到 32，于是 24..31 这 8 个字节不属于任何对象：它们是分配器的 slack，不是邻居的数据。`a[28]` 在这段里，所以它测的是一条很具体的分界线：

> tool 记住的是程序**请求**的大小，还是分配器**交出**的块？

- ASan 记请求（24），把 24..31 标成不可寻址 → 报
- LowFat 的边界是 size class（32）→ 偏移 28 在界内 → 不报
- 已标注的 arena 只有在 unpoison 恰好 n 字节（而不是 round 后的 32）时才报。`allocators/arena/arena.c` 就是这么写的，注释里也说明了原因

## 内存布局
```
arena (16 对齐):  [ a: 请求 24 | slack 24..31 ][ b: 24 | slack ]
                                   ^ a[28] 在这里，永远到不了 b
```
在 malloc 下，glibc 对 24 字节请求的 usable size 就是 24（chunk 32，前 8 字节是 size），所以 `a[28]` 已经进了下一个 chunk 的头部；ASan 的右 redzone 先报。

## 预期结果
见 `case.json`。这是全套 case 里唯一一个"缺陷**只**落在分配器 slack 内"的 case，所以它单独把 request-granular 和 block-granular 两类 tool 分开。

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
