# 29 — corrupt page header: sqlite3Get4byte reads past the page buffer (heap over-read)

Capstone `29_fz02_btree_get4byte_page_overread`; R2 fuzz-corpus diff image fz02, trigger re-derived by capstone on 2026-10-03. No upstream ticket: the image comes from SQLite's post-3.22.0 fuzz corpus and crashes stock 3.22.0.

## 漏洞
- 类别：heap overflow；访问：read（1 字节起，`sqlite3Get4byte`）
- 对象：页缓存（pcache1）的一个页缓冲区
- 一句话：一张 1041 字节的损坏数据库镜像，`SELECT * FROM dbstat` 时 `statDecodePage` 按损坏的 cell 指针调用 `sqlite3Get4byte`，读到页缓冲区之外约 2 KB

## 触发方式
镜像内嵌在 case.c，由 `shared/repro322_memfs.c`（capstone 的内存文件系统 VFS，支持 journal）提供为 `test.db`。需要 `-DSQLITE_ENABLE_DBSTAT_VTAB`，否则语句失败于 "no such table: dbstat"，case 空过。

可达性标记：`fz02 open_rc=0`。若 `s0_rc=11`（SQLITE_CORRUPT），是引擎在到达缺陷前拒绝了镜像，记 TOOL-ERROR 而不是 MISSED。

## 三个 arm 下对象在哪
| arm | 页缓冲区来自 | 预期（ASan） | macOS 本机冒烟（不可引用） |
|---|---|---|---|
| memsys5 | 256 KiB arena | MISSED | DETECTED，但报的是 **global-buffer-overflow**：读越过了整个 arena 的末端（arena 末端后 1894 字节；arena 放大到 1 MiB 后仍越过，末端后 2708 字节） |
| default | pcache1 bulk pool（`SQLITE_DEFAULT_PCACHE_INITSZ=20` 页一次性 malloc） | MISSED | DETECTED heap-buffer-overflow（"wild pointer"，离开了整个 pool） |
| rewrite | malloc，每页一块 | DETECTED | DETECTED heap-buffer-overflow |

两个 fuzz case 的越界距离太大（约 2 KB），不论 arena 还是 bulk pool 都被整体越过，所以 ASan 在 nested arm 下也报了，只是报的是**容器**的边界而不是页的边界（`run-real.py` 在 note 里标注 "left the arena"）。这一点要如实写进报告：对这类"大步越界"的真实 bug，CMA 并不能藏住它；藏得住的是 corpus/cases 里那种 1 字节、落在邻居对象里的越界。想在真实 bug 上复现"被藏住"，需要越界距离小于页在容器中到容器末端的距离，是 A7.8 的内容。

## 对照
以 rewrite arm 下 ASan DETECTED 为 gate。
