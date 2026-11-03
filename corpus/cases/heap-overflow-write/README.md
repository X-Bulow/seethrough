# heap-overflow-write (case 0)

## 漏洞
- 类别：heap overflow　访问：write
- 一句话：对一个 24 字节对象 `a` 写 `a[24]`，越过末尾 1 字节。

## 触发方式
- `st_alloc(24)` → a；`st_alloc(24)` → b；两者都 memset 成 0x5a
- 非法访问：`a[24] = 1`，偏移 24（紧接末尾第一个字节）

## 内存布局
```
malloc:   [hdr][ a: 24 bytes ][pad 8][redzone (ASan)]  [hdr][ b ... ]
          a[24] 落在 pad / redzone，ASan 的 shadow 标记为不可访问 → 报

arena:    [ a: 24 bytes ][ b: 24 bytes ][ ... ]
          a[24] == b[0]，整块 arena 对 ASan 来说都是可访问的 → 不报
          标注后：分配 a 时只 unpoison a 的 24 字节，b[0] 之前的字节仍 poisoned → 报
          （若 arena 按 16 对齐，a 实际占 32，a[24..31] 是 slack；标注时要把 slack 也 poison）

freelist: 同 size class 连续排列，同上
```

## 预期结果和理由
见 `case.json` 的 `expected`。要点：这个 case 测的是"tool 的边界粒度"，不是"tool 能否看到堆"。

## 对照组
- `-DST_NEGATIVE_CONTROL` 把 `a[24] = 1` 换成 `a[23] = 1`，分配和释放完全相同。
