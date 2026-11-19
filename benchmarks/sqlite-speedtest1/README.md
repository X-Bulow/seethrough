# SQLite speedtest1

Measures SQLite 3.50.4 overhead with default allocation and memsys5.

- [fetch.sh](fetch.sh) — download and verify source
- [build.sh](build.sh) — build baseline and ASan binaries
- [run.sh](run.sh) — default-allocation measurements
- [run-memsys5.sh](run-memsys5.sh) — memsys5 measurements

Run these scripts in order from the repository root. Each runner writes a new results bundle. This benchmark uses a different SQLite version from the defect corpus and allocator adapters.
