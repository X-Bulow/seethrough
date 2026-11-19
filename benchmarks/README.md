# Benchmarks

Measure elapsed time and peak memory relative to an uninstrumented baseline.

| Workload | Purpose |
|---|---|
| [sqlite-speedtest1](sqlite-speedtest1/README.md) | SQLite default versus memsys5 allocation |
| [lua](lua/README.md) | Interpreter tool overhead |
| [allocator-churn](allocator-churn/README.md) | Annotation and rewrite overhead |

[plot.py](plot.py) summarizes five-run medians and generates figures from one benchmark's CSV files. Install [requirements.txt](requirements.txt), then run:

```bash
python3 benchmarks/plot.py results/<bundle>/benchmark.csv
```

Keep workloads and host environments separate when comparing results.
