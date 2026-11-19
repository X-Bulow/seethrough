# Report

LaTeX source and generated artifacts for the final report.

- [src/main.tex](src/main.tex) — report entry point
- [src/refs.bib](src/refs.bib) — bibliography
- [scripts/gen.py](scripts/gen.py) — table generation
- [scripts/check-repro.py](scripts/check-repro.py) — artifact verification
- `tables/`, `figures/` — generated artifacts
- `build/` — PDF and build outputs

Run `make -C report` to build the PDF (requires latexmk and TeX). Use `make -C report tables` to regenerate tables. See the [reproducibility guide](../docs/reproducibility.md) for verification.
