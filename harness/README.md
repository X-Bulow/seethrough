# harness (Part A)

| file | role |
|---|---|
| `main.c` | the `main()` linked into every case image; prints `ST BEGIN` / `ST DONE` |
| `run-matrix.py` | enumerates tool x alloc x annot x case x {bug, control}, builds via `make image`, runs, classifies, writes `matrix.csv` |
| `classify.py` | output + exit code → verdict; one regex per tool |
| `render-matrix.py` | TODO(A4.5): `matrix.csv` → the Detection Matrix table for the report |

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

## A bundle is never edited

`results/<bundle>/` holds `env.txt`, `matrix.csv`, and one `.stdout` / `.stderr` per run. If
something was wrong, make a new bundle and say in `results/README.md` why the old one is
superseded. Verdicts copied into a `case.json` name the bundle they came from.
