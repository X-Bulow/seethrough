# 19 — DELETE on an R-Tree while a cursor is open (use-after-free read)

Capstone `19_c8c9cdd9dd_rtree_cursor_stale_node`; upstream fix c8c9cdd9dd, released in SQLite 3.24.0 (SQLITE_LOCKED_VTAB).

## 漏洞
- 类别：use after free；访问：read（4 字节，`pNode->nRef`，位于 488 字节 RtreeNode 偏移 16）
- 对象：`RtreeNode`，`sqlite3_malloc` 分配，挂在打开游标的 search-point 栈里
- 一句话：游标扫到第 3 行时在同一张 rtree 上执行 `DELETE`，`rtreeDeleteRowid → nodeRelease/removeNode` 释放了游标还持有的节点；下一次 `sqlite3_step` 在 `rtreeNext → rtreeSearchPointPop → nodeRelease` 读已释放节点

## 触发方式
`PRAGMA page_size=512` 让 30 行就形成两层树（`t1_node` 有 3 个节点；一层树什么都不会释放，case 会空过）。嵌套 DELETE 返回 0 就是漏洞存在的证据：修复后的引擎返回 SQLITE_LOCKED_VTAB。需要 `-DSQLITE_ENABLE_RTREE -DSQLITE_RTREE_INT_ONLY`。

可达性标记：`rtreecursor nested delete rc=0`。

## 三个 arm 下对象在哪
| arm | RtreeNode 来自 | 预期（ASan） | macOS 本机冒烟（不可引用） |
|---|---|---|---|
| memsys5 | 256 KiB arena | MISSED | MISSED，随后 SEGV（见下） |
| default | malloc（488 字节 `sqlite3_malloc`，不是连接私有的 lookaside 对象） | DETECTED | DETECTED |
| rewrite | malloc | DETECTED | DETECTED |

memsys5 arm 下的 SEGV：节点释放回 memsys5 后，块体前 8 字节被写成 free-list 的 `Mem5Link{next,prev}`，随后的 stale read 读到的是分配器元数据，再解引用得到地址 0x2。ASan 打印的是 `SEGV on unknown address`，这是它的信号处理函数在报崩溃，不是检测。`harness/classify.py` 把这类报告记为 MISSED 并注明 crashed。这正是报告里要说的点：CMA 把一个本来可见的 UAF 变成了一次迟到的、位置随机的崩溃。

## 对照
同 03：以 rewrite arm 下 ASan DETECTED 为 gate。

## Formal results (2026-11-16)

| tool | memsys5 | default | rewrite |
|---|---|---|---|
| asan | MISSED (SEGV) | DETECTED | DETECTED |
| valgrind | DETECTED | DETECTED | DETECTED |

Lab server, x86-64 (`results/2026-11-16-lab-real`, commit `2098f2a`). memsys5 hides the stale read from both tools. The read itself is silent; a pointer loaded from the stale node is then 0x2 and the program faults on the zero page. ASan's signal handler reports the SEGV (MISSED, crashed: A7.6 confirmed on the server); Memcheck reports an invalid read at address 0x2 and then SIGSEGV, which the harness records as DETECTED, but it is the same crash, not a report on the node. Default and rewrite: both tools report the read 24 bytes into the freed 496-byte node.
