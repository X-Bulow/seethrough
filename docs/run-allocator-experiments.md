# Running the allocator experiments on a Linux VM

`tools/run-allocator-experiments.sh` runs the constructed-case detection matrix and allocator-churn benchmark on x86-64 Linux. Run it from the repository root:

```bash
bash tools/setup-server.sh
bash tools/run-allocator-experiments.sh results/$(date +%F)-server
```

The installer pins packages for Ubuntu 26.04. On another distribution or release, install clang, gcc, make, Python 3, Valgrind, libc development headers, curl, unzip, and GNU time with that system's package manager instead. Preserve the actual tool versions recorded in each bundle's `env.txt`.

## Runner stages

The script downloads the pinned SQLite 3.53.3 source, then runs ASan and Valgrind over four groups of all 16 constructed cases:

| Output suffix | Allocators | Annotation settings |
|---|---|---|
| `-core` | malloc, arena, freelist | off and on |
| `-memsys5` | SQLite memsys5 | off and on |
| `-lookaside` | SQLite lookaside | off only |
| `-rewrite` | arena-rewrite, freelist-rewrite | off only |

Each bug executable has a paired negative control. Before running cases, the harness requires the tool to detect the malloc overflow and use-after-free positive controls. A failed positive control prevents verdicts for that tool. Detection bundles contain `matrix.csv`, raw outputs, and `env.txt`. The script refuses to overwrite an existing detection bundle.

Finally, the script invokes `benchmarks/allocator-churn/run.sh`. Its default configuration produces 90 benchmark rows: five runs for each combination of three tools and six allocator/annotation settings. It writes a separate dated bundle containing `benchmark.csv`, raw timing and output files, and `env.txt`.

## Plotting and interpretation

```bash
python3 benchmarks/plot.py results/<allocator-churn-bundle>/benchmark.csv \
  --out-dir build/churn-figures --summary build/churn-summary.csv \
  --environment-label '<OS and hardware used for this run>'
```

Compare annotation on/off within the same allocator and tool. Rewrite arms change lifetime and reuse semantics, so interpret them separately. Lookaside has no verified annotation patch and rejects annotated builds. A sanitizer's signal-only SEGV report is classified as a crash without defect detection. See [harness/README.md](../harness/README.md) for verdicts and [benchmarks/allocator-churn/README.md](../benchmarks/allocator-churn/README.md) for benchmark controls.
