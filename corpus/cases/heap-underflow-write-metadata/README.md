# 7 heap-underflow-write-metadata — 覆写 header 所在的 8 字节

## 漏洞
- 类别：heap underflow　访问：write
- 对象：`a`，24 字节；写覆盖 `a-8 .. a-1`
- 一句话：覆写分配器放"大小"的那 8 个字节

## 这是 capstone memsys5 演示案的 ground-truth 版本
把簿记信息放在用户块**旁边或里面**（in-band）的分配器，会把一次小小的越界写变成对分配器自身的破坏：
- glibc 把 chunk size 放在 `p - 8`
- memsys5 把 free-list 链接写在**已释放块的块体内部**（`capstone/bug-corpora/sqlite/engine-repros/18_mem5-design_*`）

所以同一行源码在不同分配器下含义完全不同，这正是要测的：
| 分配器 | `a-8 .. a-1` 是什么 | 后果 |
|---|---|---|
| malloc | chunk header（size） | ASan 的左 redzone 先报；不挂 tool 时 `free()` 可能 abort |
| bump arena | 没有 header，只是 `first` 的 slack | 谁都不会注意到 |
| free list（B1.3） | 也只是 `first` 的 slack：记账在 pool 外的 side table，链接字只写进已释放的 slot | 未标注时谁都不会注意到；已标注时这段是 poison 的，检出 |

`none`（不挂任何 tool）这一列在这个 case 里特别有信息量：它记录程序有没有稍后在分配器内部崩掉。

## 内存布局
```
arena:   [ first: 24 | slack 24..31 ][ a: 24 | slack ]
                         ^^^^^^^^ 这 8 字节就是 a-8..a-1
glibc:   [ prev_size | size (8B) ][ a: 24 ...
                       ^^^^^^^^ a-8..a-1
```

## 预期结果
见 `case.json`。free list 的已标注列原先标了 to verify，取决于 B 的实现有没有 in-band header。B1.3 的 free list 没有：`a-8..a-1` 是 `first` 的 slack，已标注时是 poison 的，本机 ASan 冒烟确认为 DETECTED。我们的两个 pool 分配器都没有 in-band header，所以这个 case 里能被写坏的分配器状态只有 glibc 的 header。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED |

## 本机冒烟（2026-11-07，合入 B1.2/B1.3 之后，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 | freelist a0 | freelist a1 |
|---|---|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED | MISSED | MISSED |

free list 已标注列确认为 DETECTED（原先标了 to verify）：B1.3 的 free list 没有 in-band header，`a-8..a-1` 是 `first` 的 slack，已标注时一直是 poison 的。
