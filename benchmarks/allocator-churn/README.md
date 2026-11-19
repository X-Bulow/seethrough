# Allocator churn

Measures annotation and rewrite costs under repeated allocation, reuse, and free.

- [churn.c](churn.c) — workload
- [run.sh](run.sh) — experiment runner and configuration

Run `bash benchmarks/allocator-churn/run.sh` from the repository root. Compare annotation settings within the same tool and allocator; rewrites change allocation behavior and are a separate comparison.
