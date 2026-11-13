# Allocator annotation overhead (C5.3 handoff)

`run.sh` measures the same allocation/reuse workload for Arena and Free list,
with `ST_ANNOT=0` and `ST_ANNOT=1`, plus their rewrite arms (`ANNOT=0`). It writes C's benchmark CSV schema and
keeps raw timing, stdout, stderr, exit codes, and environment. The default is
five runs of 10000 cycles for `none`, ASan and Valgrind on Linux. The time
column is the program's high-resolution monotonic wall time for the workload;
the external `/usr/bin/time` records peak RSS and a secondary wall time.

Run from the repository root with `bash benchmarks/allocator-churn/run.sh`.
`ST_RUNS`, `ST_CYCLES`, `ST_TOOLS` and `ST_ALLOCS` can narrow a development run;
set `ST_SCRATCH=1` to keep such a run out of version control.
the report run should use the defaults on the same x86-64 VM as C's SQLite
benchmarks. Plot with `benchmarks/plot.py` using the resulting CSV.

The uninstrumented `ANNOT=1` cell has no active tool hook; it is a build
control. Compare `ANNOT=1` with `ANNOT=0` **within each tool and allocator**
to isolate the extra annotation cost. This microbenchmark does not replace
SQLite `speedtest1` or its memsys5 results.
