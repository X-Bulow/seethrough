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
| free list | 可能是它自己的 header 或链接 | 破坏分配器状态，后果出现在很远的地方 |

`none`（不挂任何 tool）这一列在这个 case 里特别有信息量：它记录程序有没有稍后在分配器内部崩掉。

## 内存布局
```
arena:   [ first: 24 | slack 24..31 ][ a: 24 | slack ]
                         ^^^^^^^^ 这 8 字节就是 a-8..a-1
glibc:   [ prev_size | size (8B) ][ a: 24 ...
                       ^^^^^^^^ a-8..a-1
```

## 预期结果
见 `case.json`。free list 的已标注列标了 to verify：取决于 B 的实现会不会把自己的 header 也 poison 掉（应该要，分配器私有字节对用户来说本就不可寻址）。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED heap-buffer-overflow | MISSED | DETECTED use-after-poison |
| none | MISSED | MISSED | MISSED |
