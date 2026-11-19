# Reproducing results and report artifacts

There are two workflows: regenerate report artifacts from committed measurements, or rerun the experiments to collect new measurements.

## Regenerate existing artifacts

From the repository root, install the plotting dependencies and run the check:

```bash
python3 -m pip install -r benchmarks/requirements.txt
python3 report/scripts/check-repro.py
```

The check copies the required sources and result bundles into an isolated `build/report-repro-*` directory. It regenerates tables, CSV summaries, and plots, runs the detection audits, and compares generated tables and PNGs with the committed artifacts. It does not compile or execute the defect or benchmark programs.

To update the report tables and build the PDF:

```bash
make -C report tables
make -C report
```

The PDF build requires latexmk and a TeX distribution. See [report/README.md](../report/README.md) for targets and output paths.

## Collect new measurements

Use a Linux environment with the required compiler and detector installed. [tools/README.md](../tools/README.md) describes tool setup; [environment.md](environment.md) lists the environments used for committed results.

- Run the constructed-case matrix with `harness/run-matrix.py`; see [harness/README.md](../harness/README.md).
- Run the real SQLite defects with `harness/run-real.py`; see [corpus/real/README.md](../corpus/real/README.md).
- Run the combined allocator matrix and churn workload using [run-allocator-experiments.md](run-allocator-experiments.md).
- Build and run the application benchmarks using [benchmarks/README.md](../benchmarks/README.md) and its workload guides.
- For HWASan and LowFat, use the separate environments in [hwasan.md](hwasan.md) and [lowfat.md](lowfat.md).

Write each run into a new results bundle. Keep its CSV, `env.txt`, raw outputs, exit codes, and timing files together: audit and report scripts consume these files. Compare performance within the same host, workload, and configuration; do not combine measurements across machines as if they shared a baseline.
