# 12 use-after-pool-destroy-read — 整个 pool 的生命周期结束后读

## 漏洞
- 类别：use after free　访问：read
- 对象：`a`，24 字节，**从未被单独释放**；`st_alloc_fini()` 释放了它所在的整个 pool
- 一句话：对象没有被释放，容器被释放了，而指针活下来了

## 这是唯一一个"因为有 CMA 才存在"的缺陷
这就是 PostgreSQL 的 `MemoryContextReset`、Apache 的 `apr_pool_destroy`、以及每个 arena 的"请求结束时一次性全部释放"。让 arena 有吸引力的那个用法，正是制造这个 bug 的那个用法。而且这里完全没有"按对象簿记"这回事 —— 本来就没有。

## 结论是一个漂亮的不对称
> arena **藏住**发生在 pool 内部的访问，**暴露**发生在 pool 之后的访问。

因为 pool 自己就是一个 malloc 块，它的生命周期 malloc 粒度的 tool 是看得见的。所以这一行不需要任何标注就能报出来，已标注列也不会更好。它是 case 8 的镜像：case 8 是 arena 下最难的一行，case 12 是最容易的一行，而两者的缺陷类别相同。

## 前置条件
`ST NOTE pool=1` 表示分配器真的有一个 pool。malloc 下 `st_alloc_fini` 是空操作，对象照旧活着，这次读**是合法的** —— 本机冒烟一跑就暴露了这一点（最初预测是 DETECTED，实际 MISSED，因为什么都没发生）。于是加上了 `requires`：malloc 那一列按构造就是 UNSUPPORTED，它的等价物是 case 9。

`st_alloc_fini()` 在这个 case 里被调用一次，`harness/main.c` 事后还会再调一次，所以 `alloc.h` 要求所有分配器的 `st_alloc_fini` **幂等**（已给 arena 加上 `if (!base) return;`）。

## 触发方式
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
printf("ST NOTE pool=%d\n", st_alloc_pool_bytes() > 0);
st_alloc_fini();               // pool 的生命周期结束，a 从未被释放
st_sink(a[0]);                 // 缺陷
```
对照组把读移到 `st_alloc_fini()` 之前。

## 预期结果
见 `case.json`：asan / valgrind / hwasan 在 arena 和 freelist 的所有列都是 DETECTED，malloc 列 UNSUPPORTED。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | UNSUPPORTED（没有 pool） | DETECTED heap-use-after-free | DETECTED heap-use-after-free |
| none | UNSUPPORTED | MISSED | MISSED |

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | UNSUPPORTED（没有 pool） | DETECTED heap-use-after-free | DETECTED heap-use-after-free | DETECTED heap-use-after-free | DETECTED heap-use-after-free |
| none | UNSUPPORTED | MISSED | MISSED | MISSED | MISSED |

free list 两列和 arena 两列结论相同。
