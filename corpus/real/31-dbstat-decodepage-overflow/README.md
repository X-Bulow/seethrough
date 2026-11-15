# 31 — corrupt page: statDecodePage's cell-pointer walk leaves the page buffer (heap over-read)

Capstone `31_fz10_dbstat_decodepage_overflow`; R2 fuzz-corpus diff image fz10, trigger re-derived by capstone on 2026-10-03.

## 漏洞
- 类别：heap overflow；访问：read（`statDecodePage`，sqlite3.c:177956）
- 对象：页缓存（pcache1）的一个页缓冲区
- 一句话：595 字节的损坏镜像，`SELECT * FROM dbstat` 时 dbstat 虚表遍历 cell 指针数组，指针指到页缓冲区之外

与 29 的区别：29 的越界读在 btree 层的 `sqlite3Get4byte`（dbstat 只是调用者），31 的越界读在 dbstat 扩展自己的解码循环里。

## 触发方式
同 29：内嵌镜像 + `shared/repro322_memfs.c`，`-DSQLITE_ENABLE_DBSTAT_VTAB`。可达性标记：`fz10 open_rc=0`。

## 三个 arm 下对象在哪
| arm | 页缓冲区来自 | 预期（ASan） | macOS 本机冒烟（不可引用） |
|---|---|---|---|
| memsys5 | 256 KiB arena | MISSED | DETECTED global-buffer-overflow，arena 末端后 2200 字节（1 MiB arena 同样越过） |
| default | pcache1 bulk pool | MISSED | DETECTED heap-buffer-overflow（wild pointer） |
| rewrite | malloc，每页一块 | DETECTED | DETECTED heap-buffer-overflow |

结论同 29：越界步长太大，容器边界替页边界报了警。见 29 的 README。

## 对照
以 rewrite arm 下 ASan DETECTED 为 gate。

## Formal results (2026-11-16)

| tool | memsys5 | default | rewrite |
|---|---|---|---|
| asan | DETECTED | DETECTED | DETECTED |
| valgrind | MISSED | DETECTED | DETECTED |

Lab server, x86-64 (`results/2026-11-16-lab-real`, commit `2098f2a`). memsys5: Memcheck silent (the arena is a static array and Memcheck has no redzones around global data); ASan reports a global-buffer-overflow 34,968 bytes after the 256 KiB arena sqlite_heap, i.e. the arena's bound, not the page's. Default and rewrite: both report, ASan in heap redzone memory (wild pointer), Memcheck 12 KB (default) and 51 KB (rewrite) into unallocated heap: the read strides far past the page in every arm.
