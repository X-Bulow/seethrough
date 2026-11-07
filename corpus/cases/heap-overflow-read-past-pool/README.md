# 4 heap-overflow-read-past-pool — 读到分配器自己那块内存之外

## 漏洞
- 类别：heap overflow　访问：read
- 对象：`a`，24 字节；访问点是 `a + st_alloc_pool_bytes() + 8192`
- 一句话：读到 CMA 向 malloc 要的那一整块的**外面**

## 这个 case 是其他越界行的对照
一次越界如果停在 pool 内部，malloc 粒度的 tool 看不见；一次越界如果**离开** pool，那它就是对分配器自己那一个 malloc 块的普通越界，所有 tool 都恢复视力。

所以这一行报出来**不能**说明 tool 理解了自定义分配器，只能说明它不需要理解。报告里必须把这一点写清楚，否则矩阵里这一行会被误读。

它也是 `corpus/real` 里 29、31 两个真实 SQLite fuzz case 的 Tier-1 对应物：那两个镜像越界约 2 KB，直接越过了整个 256 KiB 的 memsys5 arena，ASan 报的是 arena 这个全局数组的边界。

## 偏移量是算出来的，不是写死的
```c
size_t pool = st_alloc_pool_bytes();
size_t off  = pool ? pool + 8192 : 24;
st_sink(a[off]);
```
每个 `st_alloc` 的结果都在 pool 的基址之后，所以 `a + pool + 8192` 一定在 pool 末尾之外，不管 a 落在 pool 的哪个位置。原先的 `+64` 在 Linux Valgrind 开发环境中恰好落到紧邻 pool 的元数据分配块，造成假漏报；改为 `+8192` 后，ASan 和 Valgrind 都报告池边界越界。这个距离仍需在正式服务器复核。`st_alloc_pool_bytes()` 是为这个 case 加进 `alloc.h` 的（A2.7），没有 pool 的分配器返回 0。

malloc 没有 pool，这时"容器"就是对象本身，偏移退化成 24，case 退化成 case 1 —— 这一列必须 DETECTED，它是整行的基线。

## 预期结果
见 `case.json`。LowFat 在 malloc 列**不报**（偏移 24 在 size class 内，同 case 1），在 arena 列报。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow |
| none | MISSED | MISSED | MISSED |

旧冒烟使用 `+64`；上表仅记录当时的开发结果。新偏移的 `ST NOTE` 会在后续运行的 stdout 中保留，便于复核。

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow | DETECTED heap-buffer-overflow |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

这次用的是 `+8192` 的偏移：arena 和 free list 下 stdout 记的是 `ST NOTE pool_bytes=1048576 offset=1056768`，malloc 下退化为 `offset=24`。free list 两列和 arena 两列一样，都报 pool 之外的越界。
