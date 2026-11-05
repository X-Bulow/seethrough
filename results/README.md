# results

One directory per run: `YYYY-MM-DD-<label>/` with `env.txt`, `matrix.csv` (`real.csv` for `corpus/real/`, or the benchmark
CSV) and the raw `.stdout` / `.stderr` of every run. Written by `harness/run-matrix.py`, `harness/run-real.py` or
`benchmarks/*/run.sh`, committed as-is, never edited.

| bundle | what | status |
|---|---|---|
| (none yet) | | |

`scratch-*/` bundles are gitignored: laptop smoke runs go there and never into the table.

A superseded bundle stays and gets a line here saying what replaced it and why.
