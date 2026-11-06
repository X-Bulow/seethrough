# 13 double-free — 同一个指针释放两次

## 漏洞
- 类别：double free　访问：free
- 对象：`a`，24 字节；另外分配 `b`，只为了让对照组有第二次合法的 free
- 一句话：`st_free(a)` 之后再 `st_free(a)`

## 触发方式
```c
a = st_alloc(24);  b = st_alloc(24);
st_free(a);
ST_READY();
st_free(a);        // 缺陷。b 留给 st_alloc_fini
```
对照组第二次释放的是 `b`。**两个 image 都正好调用两次 `st_free`** —— 这一点必须保证，否则一个"在第三次 free 调用上报错、第二次不报"的 tool 会被误当成检测器。代价是 bug image 漏掉了 b（一次泄漏），所以 Valgrind 用 `--leak-check=no` 跑。

## CMA 下这个"缺陷"可能根本不成立
| 分配器 | 第二次 free 发生了什么 |
|---|---|
| malloc | libc 发现 chunk 已在 free list 上，ASan 报 `attempting double-free` |
| bump arena | `st_free` 是空操作，第二次调用什么也没做，没有状态可破坏 |
| free list | 同一块被压入链表两次，分配器从此承诺把一个地址交给两个调用者 → case 15 |

程序确实违反了分配器的契约，但 arena 没有可被破坏的状态，所以任何 tool 都看不到。这是一个诚实的 MISSED：缺陷在程序里，arena 的"宽容"才是没人报的原因。

## 这一行区分了两套标注接口的表达能力
> ASan 的 `POISON` / `UNPOISON` 描述的是**可寻址性**；double free 错在**所有权**，而且根本没有访问可供插桩。所以无论怎么 poison，ASan 的标注接口都表达不了它。
>
> Valgrind 的 `MEMPOOL_FREE` 描述的是**分配身份**：释放一个 pool 当前并不持有的块会被报出来。

于是已标注列里 ASan 是 MISSED，Valgrind 的 free list 列是 DETECTED（arena 永远不调 `MEMPOOL_FREE`，所以仍然 MISSED）。这是报告里比较两套接口的核心例子。

## 预期结果
见 `case.json`。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED `attempting double-free` | MISSED | **MISSED** |
| none | MISSED | MISSED | MISSED |

已标注 arena 仍然 MISSED，和"poison 表达不了所有权"的预测一致。Valgrind 那一列要在服务器上测（本机没装）。
