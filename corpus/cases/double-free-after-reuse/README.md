# 15 double-free-after-reuse — 重用之后再释放，把活对象的块从它脚下释放掉

## 漏洞
- 类别：double free　访问：free
- 对象：`a` 24 字节被释放；`b = st_alloc(24)` 拿到 a 的存储；`st_free(a)` 释放的其实是 b 的块
- 一句话：第二次 free 看起来完全合法，被破坏的是"谁拥有这块内存"

## 为什么 double free 要拆成两个 case
```c
a = st_alloc(24);  st_free(a);
b = st_alloc(24);              // free list 用 a 的存储满足它，b == a
printf("ST NOTE reuse=%d\n", b == a);
st_free(a);                    // 缺陷：释放的是分配器眼里还活着、属于 b 的地址
st_sink(b[0]);                 // b 现在是一个已释放的块
```
在立刻重用的 free list 上，`a == b`，所以第二次 free 和"正确地释放 b"**无法区分**：没有任何 tool 能对它提出异议。缺陷只有在 b 之后被使用时才显形 —— 也就是这个 case 结尾那次读。

所以这一行的检测**来自那次读，而不是来自 free**，报告里必须这么写。对比 case 13：那里两个指针不同（malloc 有 quarantine），第二次 free 本身就是 double free。

## 和 case 10 的对比：这一次标注赢了
case 10 的访问发生时内存是活的，标注无能为力。这里不同：缺陷的那次 free 在已标注的实现里会**poison b 的存储**，紧接着的读就是一次对 poisoned 内存的访问 → 报出来。

> 同一个"一个地址两个所有者"的局面，标注能不能救回来，取决于错误操作是**访问**还是**释放**：释放会留下一个可以涂色的痕迹，访问不会。

## 前置条件
`ST NOTE reuse=1`；没有重用时这就是 case 13。ASan 的 quarantine 和 arena 的不重用让那些列按构造就是 UNSUPPORTED（见 case 10 的说明）。

## 预期结果
见 `case.json`：free list 的未标注列 MISSED，已标注列 DETECTED（经由那次读）。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | UNSUPPORTED（quarantine，未重用） | UNSUPPORTED（arena 不重用） | UNSUPPORTED |
| none | MISSED（已重用，无 tool 可报） | UNSUPPORTED | UNSUPPORTED |

当时没有会重用的分配器，真正的测量要等 B1.3 的 free list，见下一节。

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | UNSUPPORTED（quarantine，未重用） | UNSUPPORTED（arena 不重用） | UNSUPPORTED | MISSED | DETECTED use-after-poison |
| none | MISSED（已重用，无 tool 可报） | UNSUPPORTED（arena 不重用） | UNSUPPORTED | MISSED | MISSED |

free list 前置条件满足。未标注 MISSED；已标注时那次过期的 free 把 `b` 的存储 poison 掉，随后的读被报成 use-after-poison，所以 DETECTED。和预测一致：检出来自那次读，不是来自 free。
