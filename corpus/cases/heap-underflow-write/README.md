# 5 heap-underflow-write — 越界写前 1 字节

## 漏洞
- 类别：heap underflow　访问：write
- 对象：`a`，24 字节，在另一个 24 字节对象 `first` 之后分配
- 一句话：写 `*(a - 1)`

## 为什么 underflow 要和 overflow 分开
对这几个 tool 来说，一个对象的两侧并不对称：
- bump-pointer arena 的左邻居是**更早**分配的对象，右邻居是更晚的
- free list 的左侧常常是它自己的 free-list 链接或 header
- ASan 的左 redzone 和右 redzone 由不同的插桩检查
- **LowFat 对 underflow 比 overflow 准**：对象基址对齐到它的 region，所以基址以下一定越界；而 size class 内的 overflow 不越界。case 5 报、case 1 不报，就是这个原因

在 malloc 下 `*(a-1)` 是 chunk header 的最后一个字节，libc 在 `free()` 时还会读回来，所以即使不挂 tool 程序也可能稍后崩溃 —— `none` 那一列值得看。

## 内存布局
```
arena (16 对齐):  [ first: 24 |slack 24..31 ][ a: 24 |slack ]
                                        ^31       ^32
                  *(a-1) 就是 first 的最后一个 slack 字节
                  未标注：可寻址 → 不报
                  已标注：first 分配时只 unpoison 24 字节 → 31 仍 poisoned → 报
```

## 预期结果
见 `case.json`。

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

free list 两列和 arena 两列结论相同。
