# 11 use-after-realloc-read — realloc 搬走对象之后读旧指针

## 漏洞
- 类别：use after free　访问：read
- 对象：`a` 24 字节，被 `st_realloc(a, 4096)` 扩大；realloc 搬家时释放了旧块
- 一句话：源码里**看不到任何 free**，但旧指针已经失效

## 为什么单独成案
`st_realloc(p, bigger)` 可能搬家，搬家时旧块被释放。调用之前取到的指针事后就是悬垂的 —— 这是真实程序里最常见的 UAF 来源之一，而且因为源码里没有 `free()`，code review 很难看出来：
- SQLite 的 agginfo 缺陷（capstone case 01）就是这个形状
- PostgreSQL 的 `repalloc` 相关几行同理

它和 case 8、9 的区别在于：结束生命周期的动作在**分配器内部**，所以一个分配器可以独立地把它做对或做错 —— 原地扩张的 arena 根本没有这个缺陷，而会复制的分配器必须在搬家时 poison 旧块。

## 前置条件
`ST NOTE realloc=1 moved=1` 表示调用成功**且**对象真的搬了家。`case.json` 的 `requires` 盯住 `moved=1`：
- arena 和 free list 的 `st_realloc` 都是"新分配、复制、`st_free` 旧块"，总是搬家（arena 自 B1.2 起；之前返回 NULL，整列 UNSUPPORTED）
- 原地扩张成功的分配器 `moved=0` → 旧指针仍然有效，没有缺陷可报

## 触发方式
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
big = st_realloc(a, 4096);     // 搬家，旧块被释放
st_sink(a[0]);                 // 缺陷
```
对照组读 `big[0]`。

## 预期结果
见 `case.json`。LowFat 整行 UNSUPPORTED（只查边界）。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-use-after-free | UNSUPPORTED（无 realloc） | UNSUPPORTED |
| none | MISSED | UNSUPPORTED | UNSUPPORTED |

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-use-after-free | **MISSED** | **DETECTED use-after-poison** | MISSED | DETECTED use-after-poison |
| none | MISSED | **MISSED** | **MISSED** | MISSED | MISSED |

加粗的格子与 2026-11-05 那次不同：B1.2 之前 arena 的 `st_realloc` 返回 NULL，整列 UNSUPPORTED；现在它总是搬家，未标注 MISSED，已标注 DETECTED。
