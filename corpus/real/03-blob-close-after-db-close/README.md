# 03 — sqlite3_blob_close() after sqlite3_close_v2() (use-after-free read)

Capstone `03_e464802d49_blob_close_after_db_close`; upstream fix e464802d49, released in SQLite 3.29.0.

## 漏洞
- 类别：use after free；访问：read（8 字节，`db->lookaside` 字段）
- 对象：`sqlite3` 连接结构体本身，由 `sqlite3MallocZero` 分配，即一个普通的引擎级分配，**不是** lookaside 对象
- 一句话：blob 句柄还开着时 `sqlite3_close_v2` 把连接变成 zombie；随后 `sqlite3_blob_close` 内部先 `sqlite3_finalize`（这是最后一条语句，连接被真正释放），再 `sqlite3DbFree(db, p)` 去读已释放的 `db`

## 触发方式
`:memory:` 库，一张表一行 zeroblob，`sqlite3_blob_open` 后 `sqlite3_close_v2`（必须返回 0，表示走了 zombie 路径；普通 `sqlite3_close` 返回 SQLITE_BUSY 且没有 UAF），再 `sqlite3_blob_close`。非法读在 `sqlite3DbFreeNN`（sqlite3.c:25485，3.22.0 行号）。

可达性标记：`blobclose close_v2 rc=0`。

## 三个 arm 下对象在哪
| arm | 连接结构体来自 | 预期（ASan） | macOS 本机冒烟（不可引用） |
|---|---|---|---|
| memsys5 | 256 KiB 静态 arena 内 | MISSED | MISSED |
| default | malloc（连接本身不是 lookaside 对象） | DETECTED | DETECTED |
| rewrite | malloc | DETECTED | DETECTED |

这个 case 只被 memsys5 一层挡住：default arm 下 ASan 照常报出，因为悬垂的是连接本身而不是它的 lookaside 池里的小对象。它是 corpus/cases 里 UAF-read 的真实对应物。

## 对照
没有 negative control 双胞胎。rewrite arm 下 ASan 必须 DETECTED，否则该 case 整行 UNSUPPORTED（`harness/run-real.py` 的 gate）。
