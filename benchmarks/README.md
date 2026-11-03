# benchmarks — Q2 overhead (Part C)

| directory | program | why it is here | CMA switch |
|---|---|---|---|
| `sqlite-speedtest1/` | SQLite `speedtest1` | the proposal's main benchmark; memsys5 and lookaside are compile/config switches | `-DSQLITE_ENABLE_MEMSYS5` + `SQLITE_CONFIG_HEAP`; lookaside via `SQLITE_CONFIG_LOOKASIDE` |
| `postgres/` | a regression subset | memory contexts (aset / slab) | none upstream; the rewrite question is "what would it cost" |
| `lua/` | Lua test suite or a fixed script | `lua_Alloc` is one function pointer, the easiest CMA to undo | replace `l_alloc` |

Protocol (from the proposal, kept): `-O2`, median of 5 runs, wall-clock time and peak RSS
(`/usr/bin/time -v`, `Maximum resident set size`), baseline uninstrumented, then each tool,
then each tool with annotations on. One CSV per benchmark, columns:
`bundle, benchmark, config, tool, annot, run, seconds, peak_rss_kb`. `plot.py` (TODO C5.6)
draws the figures from the CSVs and nothing else.
