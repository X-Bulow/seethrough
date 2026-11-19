# Results

Each bundle contains CSV measurements, `env.txt`, and raw output and timing files. Report generation and audits read these files directly.

| Bundle | Experiment |
|---|---|
| [2026-11-10-ec2-b-pilot/](2026-11-10-ec2-b-pilot/)  |  EC2 positive-control pilot, case 0 malloc under ASan and Valgrind |
| [2026-11-10-ec2-b-core/](2026-11-10-ec2-b-core/)  |  EC2 malloc, Arena and Free list; annotation off/on; ASan and Valgrind |
| [2026-11-10-ec2-b-memsys5/](2026-11-10-ec2-b-memsys5/)  |  EC2 SQLite 3.53.3 memsys5; annotation off/on |
| [2026-11-10-ec2-b-lookaside/](2026-11-10-ec2-b-lookaside/)  |  EC2 SQLite 3.53.3 lookaside, unannotated |
| [2026-11-10-ec2-b-rewrite/](2026-11-10-ec2-b-rewrite/)  |  EC2 Arena and Free-list libc rewrites |
| [2026-11-10-allocator-churn-IkUTIU/](2026-11-10-allocator-churn-IkUTIU/)  |  EC2 annotation overhead and rewrite performance |
| [2026-11-13-lab-core/](2026-11-13-lab-core/)  |  Lab server, formal: malloc, Arena and Free list; annotation off/on; ASan and Valgrind |
| [2026-11-13-lab-memsys5/](2026-11-13-lab-memsys5/)  |  Lab server, formal: SQLite 3.53.3 memsys5; annotation off/on |
| [2026-11-13-lab-lookaside/](2026-11-13-lab-lookaside/)  |  Lab server, formal: SQLite 3.53.3 lookaside, unannotated |
| [2026-11-13-lab-rewrite/](2026-11-13-lab-rewrite/)  |  Lab server, formal: Arena and Free-list libc rewrites |
| [2026-11-13-lima-hwasan/](2026-11-13-lima-hwasan/)  |  HWASan: malloc, Arena and Free list; annotation off/on; aarch64 Lima VM on the M5 Mac |
| [2026-11-16-lab-real/](2026-11-16-lab-real/)  |  Lab server, formal results: 4 real SQLite 3.22.0 bugs (`corpus/real`) x memsys5, default, rewrite; ASan and Valgrind |

Application benchmarks also include dated `sqlite-speedtest1` and `lua` bundles. See [environment details](../docs/environment.md) and [reproduction instructions](../docs/reproducibility.md). `scratch-*` runs are ignored.
