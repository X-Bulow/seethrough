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
| bump arena | `st_free` 是空操作，字节和释放前一样活 | **不能**：`st_free` 不知道对象多大，没法精确 re-poison（见 `allocators/arena/arena.c` 的 TODO） |
| free list | 块进 size class 链表 | 能：知道 size class，可以 poison 整块 |

所以标注这条手段会因为**分配器设计**而失败，不是因为 tool 不支持。这是报告里"annotation feasibility"一节的主要例子，也是 B2.3 要记录的内容。

## 预期结果
见 `case.json`。LowFat 整行 UNSUPPORTED：它只查边界，没有生命周期概念。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-use-after-free | MISSED | **MISSED** |
| none | MISSED | MISSED | MISSED |

已标注 arena 仍然漏报，和预测一致。等 B1.2 给 arena 加上 header 或 side table 之后，这一格应该变成 DETECTED，届时要重跑并在 `measured` 里同时保留两次结果 —— 那个差值本身就是"标注的代价是什么"的答案。
