# Tool setup

| File | Purpose |
|---|---|
| [setup-server.sh](setup-server.sh) | Install pinned Ubuntu 26.04 tool versions |
| [flags.mk](flags.mk) | Compiler and linker settings |
| [fetch-sqlite.sh](fetch-sqlite.sh) | Download and verify pinned SQLite source |
| [env.sh](env.sh) | Record the experiment environment |
| [hwasan-check.sh](hwasan-check.sh) | Probe HWASan support |
| [run-allocator-experiments.sh](run-allocator-experiments.sh) | Run allocator detection and churn experiments |
| [VERSIONS.txt](VERSIONS.txt) | Recorded tool versions |

See the [VM runner guide](../docs/run-allocator-experiments.md), [HWASan guide](../docs/hwasan.md), and [LowFat guide](../docs/lowfat.md) for platform-specific instructions.
