# Lua benchmark

Measures tool overhead using a fixed allocation, sorting, and garbage-collection workload with Lua 5.4.9's original allocator.

- [build.sh](build.sh) — download, verify, and build
- [run.sh](run.sh) — run baseline, ASan, and Valgrind measurements
- [workload.lua](workload.lua) — benchmark workload

From the repository root:

```bash
bash benchmarks/lua/build.sh
bash benchmarks/lua/run.sh
```

Outputs go to a new `results/<date>-lua-<suffix>/` bundle.
