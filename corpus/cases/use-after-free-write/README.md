# 8 use-after-free-write — 释放后写，中间没有任何分配

## 漏洞
- 类别：use after free　访问：write
- 对象：`a`，24 字节，释放后再写
- 一句话：`st_free(a)` 之后执行 `a[0] = 1`

## 触发方式
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
st_free(a);
ST_READY();
a[0] = 1;              // 缺陷
```
对照组：同样一次分配、一次释放，只是把写**移到 free 之前**。两个 image 的分配流量逐字节相同，差别只有访问与 free 的先后。

## 这一行测的是"标注做不做得到"，不是"tool 支不支持"
中间没有任何分配，所以 tool 唯一能依据的事实就是"生命周期结束了"。而这恰恰是 CMA 不记录的东西：

| 分配器 | 释放时发生了什么 | 已标注列能不能救回来 |
|---|---|---|
| malloc | 块进 quarantine，ASan 把 shadow 涂成 freed | — |
| 纯 bump arena（B1.2 之前） | `st_free` 是空操作，字节和释放前一样活 | **不能**：`st_free` 不知道对象多大，没法精确 re-poison |
| arena + side table（B1.2） | side table 记下每个对象的大小和存活状态，`st_free` 按大小 re-poison | **能**，代价是分配器多了一份逐对象的记账 |
| free list | 块进 size class 链表 | 能：知道 size class，可以 poison 整块 |

所以标注能不能生效取决于**分配器设计**，不取决于 tool 支不支持：纯 bump arena 不记对象大小，标注救不回来；B1.2 给 arena 加了一张 pool 外的 side table 之后才救得回来。标注的代价不只是几行宏，还包括分配器原本不需要的逐对象记账。这是报告里"annotation feasibility"一节的主要例子，也是 B2.3 要记录的内容（见 `docs/allocator-annotations.md`）。

## 预期结果
见 `case.json`。LowFat 整行 UNSUPPORTED：它只查边界，没有生命周期概念。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | **MISSED** |
| none | MISSED | MISSED | MISSED |

当时已标注 arena 仍然漏报，和预测一致；README 里写好了 B1.2 之后要重跑并保留两次结果，见下一节。

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | **DETECTED use-after-poison** | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

加粗的格子与 2026-11-05 那次不同。B1.2 给 arena 加了 side table 之后，已标注 arena 在 free 时按大小 re-poison，变成 DETECTED。两次结果都保留在 `case.json` 的 `measured` 里，这个差值就是"标注的代价是什么"的答案：不只是几行宏，还要一份逐对象的记账。
