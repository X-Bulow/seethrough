# 14 invalid-free-interior — 释放对象内部的指针

## 漏洞
- 类别：invalid free　访问：free
- 对象：`a`，24 字节；执行 `st_free(a + 8)`
- 一句话：传给 free 的不是 `st_alloc` 返回的那个指针

## 真实程序怎么走到这里
释放一个结构体成员、释放一个解析过程中前移过的指针、或者释放一个 header 归分配器所有的对象的 payload。

## 唯一一个"malloc 基线由分配器本身保证"的类别
glibc 和 ASan 都会直接拒绝：chunk header 不在它们预期的位置。所以这一行的 malloc 列不是靠 tool 的插桩报出来的，而是靠分配器自己的检查。

| 分配器 | `st_free(a + 8)` 的后果 |
|---|---|
| malloc | 立刻拒绝（ASan：`attempting free on address which was not malloc()-ed`） |
| bump arena | `st_free` 完全忽略参数，分不出 `a+8` 和 `a` |
| free list | 把 `a+8` 压进某个 size class 链表，之后交出去，该 class 里后续每个对象都与它所占的块错位 8 字节 —— 破坏是真实的，但出现在很远的地方 |

正因为 free list 的后果出现得很远，这个 case 只记录"它做了什么"，不依赖后续崩溃来证明。

## 触发方式
```c
a = st_alloc(24);  memset(a, 0x5a, 24);
ST_READY();
st_free(a + 8);    // 缺陷
```
对照组释放 `a`。两个 image 各一次分配、一次释放。

## 预期结果
见 `case.json`。已标注的 free list 列标了 to verify 的 DETECTED：`VALGRIND_MEMPOOL_FREE` 传入一个不是 pool 分配的地址会被报出来。

## 本机冒烟（2026-11-05，macOS arm64，仅供开发，不可引用）
| tool | malloc | arena a0 | arena a1 |
|---|---|---|---|
| asan | DETECTED `attempting free on address which was not malloc()-ed` | MISSED | MISSED |
| none | MISSED | MISSED | MISSED |
