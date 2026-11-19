# seethrough

**Do Memory-Safety Detectors See Through Custom Allocators?** CS5439 Assignment 2 — Cheng Zefeng, Wei Yuning, Xu Ruofan.

Memory-safety tools usually track individual allocations made through `malloc`. Custom allocators divide larger memory pools into smaller objects, which can hide object boundaries and lifetimes from those tools. An overflow or use-after-free inside a pool may therefore go undetected.

We investigate two questions:

- **Detection:** Which defects do ASan, Valgrind Memcheck, and HWASan miss with custom allocators, and how much detection can explicit tool annotations recover?
- **Overhead:** What runtime and memory costs do the tools and annotations add, and how do they compare with replacing pooled allocation with individual malloc calls?

The detection experiments run 16 constructed defects with paired controls across malloc, arena, free-list, and SQLite allocators. Four real SQLite defects test whether the same effects appear in an application. SQLite speedtest1, Lua, and an allocator-churn workload measure performance; churn isolates annotation and rewrite costs. The harness records verdicts and raw outputs, and report scripts turn the measurements into tables and figures.

## Repository layout

| Directory | Contents |
|---|---|
| [corpus](corpus/README.md) | Defect cases and controls |
| [allocators](allocators/README.md) | Allocator implementations and annotations |
| [harness](harness/README.md) | Build, run, classify, and audit tools |
| [benchmarks](benchmarks/README.md) | SQLite, Lua, and allocator-churn workloads |
| [tools](tools/README.md) | Environment setup, compiler flags, and downloads |
| [results](results/README.md) | Measurements and raw experiment outputs |
| [docs](docs/reproducibility.md) | Reproduction and platform guides |
| [report](report/README.md) | LaTeX source and generated tables and figures |

## Getting started

Run `make help` for build targets. On Linux with the required tools installed:

```bash
make case CASE=case00-heap-overflow-write TOOL=asan ALLOC=malloc ANNOT=0
```

See [tool setup](tools/README.md) and [reproducibility](docs/reproducibility.md) for complete workflows.
