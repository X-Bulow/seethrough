# Part B x86-64 VM experiment

The final Part B run used an AWS EC2 Ubuntu 26.04 x86-64 VM, commit `2763402`,
clang 21.1.8 and Valgrind 3.26.0. Its result bundles are indexed in
[results/README.md](../results/README.md). C's SQLite `speedtest1` runs used
a separate VirtualBox Ubuntu 26.04 VM. Keep the measurements labelled by
machine; the local macOS and arm64 Docker `results/scratch-*` bundles are
development checks only.

From the repository root:

```bash
bash tools/setup-server.sh
bash tools/run-part-b-server.sh results/$(date +%F)-ec2-b
```

The runner performs four complete 16-case matrices under ASan and Valgrind:
malloc/Arena/Free list with annotation off/on, SQLite memsys5 off/on,
lookaside unannotated, and both rewrite arms. Each bug run has a paired
negative control, and each tool must pass the positive controls before any
verdict is accepted. It then runs the five-repeat allocator churn benchmark
for annotation and rewrite overhead. Each detection bundle contains
`matrix.csv`, raw outputs and `env.txt`; the benchmark bundle contains
`benchmark.csv`, five raw runs per configuration and `env.txt`.

The runner refuses to overwrite existing detection bundles. Keep all bundles
in `results/` and commit them as new results. The benchmark CSV has 90 rows
and can be plotted with C's `benchmarks/plot.py` in a Python environment
with matplotlib. The report table was computed directly from the CSV's
five-run medians. Set the plotting caption for EC2 explicitly:

```bash
build/plot-venv/bin/python benchmarks/plot.py \
  results/<allocator-churn-bundle>/benchmark.csv \
  --out-dir build/part-b-figures --summary build/part-b-summary.csv \
  --environment-label 'AWS EC2 Ubuntu 26.04 x86-64'
```

Compare `ANNOT=1` versus `ANNOT=0` within each allocator and tool. The
rewrite changes semantics, so report its detection cells and performance
separately. memsys5's `ANNOT=1` uses the generated patch; lookaside has no
verified annotation arm. Check that every negative control is CLEAN and
that the positive controls are DETECTED. Investigate every TOOL-ERROR or
FALSE-POSITIVE before using counts in the report.

The EC2 data passed those gates: 352 negative controls CLEAN, zero
`TOOL-ERROR` and zero `FALSE-POSITIVE`. ASan's signal-only case-4 crashes
under Arena, Free list, unannotated memsys5 and lookaside are classified
as `MISSED crashed SEGV`, not DETECTED. Annotated memsys5 missed case 4
without a signal. `env.txt` records `git: 2763402 dirty=2` because an earlier
untracked pilot result bundle existed when the formal run started; tracked
source files were clean.

## If the available VM is Azure Ubuntu 24.04

The detection runner also works on an x86-64 Ubuntu 24.04 VM after
installing `clang`, `gcc`, `make`, `python3`, `valgrind`, `libc6-dev`, `curl`,
`unzip` and `time`. `tools/setup-server.sh` pins package versions from C's Ubuntu 26.04
VM, so **do not use that installer on 24.04**; use the 24.04 package manager
and preserve the exact package versions in `env.txt`. Run the positive
controls first, as the matrix runner does.

```bash
sudo apt-get update
sudo apt-get install -y clang gcc make python3 valgrind libc6-dev curl unzip time
bash tools/run-part-b-server.sh results/$(date +%F)-azure24-b
```

Do not combine the Azure performance ratios with C's earlier Ubuntu 26.04
SQLite figures as if they shared one machine. If Azure is selected for the
final report, rerun C5.1 and C5.2 and this B/C5.3 benchmark on that same
Azure VM, then label both the OS and hardware in the report.
