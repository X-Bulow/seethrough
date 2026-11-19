# Detection harness

Builds test configurations, checks controls, and classifies detector output.

| File | Purpose |
|---|---|
| [main.c](main.c) | Common case entry point |
| [run-matrix.py](run-matrix.py) | Constructed-case experiments |
| [run-real.py](run-real.py) | Real SQLite experiments |
| [classify.py](classify.py) | Output-to-verdict classification |
| [render-matrix.py](render-matrix.py) | Detection tables and expectation checks |
| [audit-missed.py](audit-missed.py) | Audit recorded misses and replica agreement |

From the repository root:

```bash
python3 harness/run-matrix.py --tools asan valgrind --allocs malloc arena --out results/<new-bundle>
python3 harness/render-matrix.py results/<bundle> --check
```

Use `--help` for options. Bundles contain CSV verdicts, raw outputs, and environment records; field definitions and validation rules are in the scripts.
