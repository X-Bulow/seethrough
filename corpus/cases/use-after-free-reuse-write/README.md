# 10 use-after-free-reuse-write — 存储被转交给别人之后再通过旧指针写

## 漏洞
- 类别：use after free　访问：write
- 对象：`a` 24 字节被释放；`b = st_alloc(24)` 拿到了 a 的存储；写通过 `a` 落进 `b` 的数据
- 一句话：一个地址两个所有者，写坏的是一个**活**对象

## 这是整个研究里最关键的一行：标注的天花板
```c
a = st_alloc(24);  st_free(a);
b = st_alloc(24);              // free list 直接把 a 的存储还回来，b == a
printf("ST NOTE reuse=%d\n", b == a);
a[0] = 0x22;                   // 缺陷：通过旧指针写，破坏 b 的数据
st_sink(b[0]);
```
访问发生的那一刻，这块内存**合法地活着**，属于 b，必须是 unpoisoned 的 —— 否则 b 自己的访问就会误报。所以：

> 任何基于"给内存涂颜色"的方案（ASan poison、Valgrind mempool）都无法区分指向同一个地址的两个指针。只有给**指针**本身打标签的机制才行。

这就是 HWASan 在这一行应该独立取胜的原因：旧指针仍带着 a 的 tag，而那个 granule 现在带着 b 的 tag。如果 C3 证明我们能跑 HWASan，这一格是最值得报告的。

## 前置条件
case 打印 `ST NOTE reuse=1` 表示分配器真的把存储还回来了；`case.json` 的 `requires` 让条件不满足的行记 UNSUPPORTED 而不是 MISSED。这一点在本机冒烟里立刻生效，而且**同一个 case 在不同 tool 下结论不同**：
- `asan + malloc`：ASan 的 quarantine 推迟重用，`b != a` → UNSUPPORTED
- `none + malloc`：没有 quarantine，glibc/libmalloc 立刻重用，`b == a` → 条件满足，记 MISSED
- 任何 arena：永不重用 → UNSUPPORTED

换句话说 ASan 的 quarantine 让这个场景在 malloc 上**构造不出来**，这本身就是一条结论：quarantine 是在用内存换掉一整类 aliasing 缺陷。

## 内存布局
```
free list, size class 32:
  st_free(a) → 链表头 = a
  st_alloc(24) → 弹出链表头 = a，于是 b == a
  a 和 b 是同一个地址；a 这个指针已经"过期"，但内存是活的
```

## 预期结果
见 `case.json`。要点：ASan 和 Valgrind 的已标注列都是 MISSED（天花板），HWASan 的 freelist 列标了 to verify 的 DETECTED。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | UNSUPPORTED（quarantine，未重用） | UNSUPPORTED（arena 不重用） | UNSUPPORTED |
| none | MISSED（已重用，无 tool 可报） | UNSUPPORTED | UNSUPPORTED |

当时没有会重用的分配器，真正的测量要等 B1.3 的 free list，见下一节。

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | UNSUPPORTED（quarantine，未重用） | UNSUPPORTED（arena 不重用） | UNSUPPORTED | MISSED | MISSED |
| none | MISSED（已重用，无 tool 可报） | UNSUPPORTED（arena 不重用） | UNSUPPORTED | MISSED | MISSED |

B1.3 的 free list 会立即重用，前置条件满足（`ST NOTE reuse=1`）。ASan 两列都是 MISSED：写下去的时候那块内存属于活着的 `b`，必须是 unpoison 的。和"天花板"的预测一致。
