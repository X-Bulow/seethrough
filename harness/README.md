# harness (Part A)

| file | role |
|---|---|
| `main.c` | the `main()` linked into every case image; prints `ST BEGIN` / `ST DONE` |
| `run-matrix.py` | enumerates tool x alloc x annot x case x {bug, control}, builds via `make image`, runs, classifies, writes `matrix.csv` |
| `classify.py` | output + exit code → verdict; one regex per tool; a sanitizer `SEGV`/`BUS`/... report is a crash, recorded MISSED |
| `run-real.py` | `corpus/real/` (A7): tool x arm x case over SQLite 3.22.0, builds via `make real-image`, gates on asan/rewrite, writes `real.csv` |
| `render-matrix.py` | one or more `matrix.csv` → the Detection Matrix (markdown or LaTeX; `--tools` / `--arms` pick the columns); `--check` lists cells that differ from `case.json`'s expectations |

## matrix.csv columns

| column | values |
|---|---|
| `bundle` | results directory name, `YYYY-MM-DD-<label>` |
| `tool` | asan, hwasan, ubsan, valgrind, lowfat, none |
| `alloc` | malloc, arena, freelist, memsys5, lookaside, arena-rewrite, freelist-rewrite |
| `annot` | 0 or 1 |
| `case`, `class`, `access` | from `case.json` |
| `image` | bug or control |
| `verdict` | bug rows: DETECTED, MISSED, FALSE-POSITIVE, UNSUPPORTED, TOOL-ERROR; control rows: CLEAN, DETECTED (which makes the bug row FALSE-POSITIVE), TOOL-ERROR, UNSUPPORTED |
| `note` | the tool's report kind, or why the verdict is what it is |
| `exit_code`, `seconds` | of the run |
| `stdout`, `stderr` | file names in the bundle holding the raw output |

The bug row's verdict already accounts for its control: a bug row says FALSE-POSITIVE when the
control image was reported, and TOOL-ERROR when the control never reached READY.

## real.csv columns (corpus/real)

| column | values |
|---|---|
| `tool` | as above |
| `arm` | memsys5, default, rewrite (`corpus/real/README.md`) |
| `case`, `class`, `access` | from the case's `case.json` |
| `layer` | where the object sits on this arm (`layer_by_arm`) |
| `verdict` | DETECTED, MISSED, UNSUPPORTED (build failed, or the asan/rewrite gate failed), TOOL-ERROR (reachability line missing) |
| `note` | report kind; "left the arena" when ASan hit the arena's redzone rather than the object's |

No control rows: the case's positive control is its own asan/rewrite row.

## A bundle is never edited

`results/<bundle>/` holds `env.txt`, `matrix.csv`, and one `.stdout` / `.stderr` per run. If
something was wrong, make a new bundle and say in `results/README.md` why the old one is
superseded. Verdicts copied into a `case.json` name the bundle they came from.
