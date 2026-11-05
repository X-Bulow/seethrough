#!/usr/bin/env python3
"""Build and run every corpus/real case on every (tool, arm); write results/<bundle>/real.csv.

    run-real.py --tools asan valgrind --arms memsys5 default rewrite --cases all \
                --out results/2026-11-10-server-real

Gates, in order (the Capstone corpus convention: an infrastructure failure never reads as a
measurement):
  1. per tool, the plain-malloc positive controls in corpus/controls/ must be DETECTED
     (shared with run-matrix.py), or the tool gets no rows and the script exits 75;
  2. per case, the `rewrite` arm under asan must be DETECTED. It is the case's own positive
     control: every SQLite object is its own malloc block there, so a silent run means the
     trigger did not reach the defect on this build, and the case's other rows are
     UNSUPPORTED rather than MISSED. (Needs asan in --tools and rewrite in --arms; otherwise
     the gate is skipped and the CSV says so in `note`.)
  3. per run, the case's own reachability line (case.json "reached") must appear on stdout,
     or the row is TOOL-ERROR "trigger not reached".

The engine is built by `make real-image` (one sqlite3.o per tool x arm x engine group,
cached under build/engine/). Raw stdout/stderr sit beside the CSV, named like the row.
"""
import argparse, csv, importlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
from classify import classify            # noqa: E402
rm = importlib.import_module("run-matrix")   # run(), positive_controls()

COLUMNS = ["bundle", "tool", "arm", "case", "class", "access", "layer", "verdict", "note",
           "exit_code", "seconds", "stdout", "stderr"]


def cases(selection):
    index = ROOT / "corpus" / "real"
    dirs = sorted(d for d in index.iterdir() if (d / "case.json").exists())
    if selection != ["all"]:
        dirs = [d for d in dirs if d.name in selection]
    return [(d.name, json.loads((d / "case.json").read_text())) for d in dirs]


def build(tool, arm, case_dir, out):
    cmd = ["make", "-s", "-C", str(ROOT), "real-image", f"TOOL={tool}", f"ARM={arm}",
           f"REAL={case_dir}", f"REAL_OUT={out}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr


def one(tool, arm, name, meta, bundle):
    stem = f"{name}-{tool}-{arm}"
    exe = ROOT / "build" / bundle.name / stem
    built, log = build(tool, arm, name, exe)
    if not built:
        (bundle / (stem + ".build.log")).write_text(log)
        return stem, "UNSUPPORTED", "build failed", 0, 0.0
    out, err, code, secs = rm.run(tool, exe)
    (bundle / (stem + ".stdout")).write_text(out)
    (bundle / (stem + ".stderr")).write_text(err)
    v, n = classify(tool, out, err, code)
    if v == "DETECTED" and "after global variable 'sqlite_heap'" in err:
        # memsys5 arm: the access left the 256 KiB arena and hit the redzone around the global
        # array. The tool saw the arena's bound, not the object's; the row stays DETECTED but
        # the report must say so (both fuzz cases do this, at 256 KiB and at 1 MiB).
        n += " (left the arena: caught by the arena's redzone, not the object's)"
    if v == "MISSED" and meta["reached"] not in out:
        v, n = "TOOL-ERROR", f"trigger not reached: no '{meta['reached']}' on stdout"
    return stem, v, n, code, secs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", nargs="+", required=True)
    ap.add_argument("--arms", nargs="+", default=["memsys5", "default", "rewrite"])
    ap.add_argument("--cases", nargs="+", default=["all"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    bundle = Path(a.out); bundle.mkdir(parents=True, exist_ok=True)
    subprocess.run(["bash", str(ROOT / "tools" / "env.sh")], stdout=open(bundle / "env.txt", "w"))
    tools = [t for t in a.tools if t == "none" or rm.positive_controls(t, bundle)]
    refused = [t for t in a.tools if t not in tools]
    gate = "asan" in tools and "rewrite" in a.arms
    rows = []
    for name, meta in cases(a.cases):
        results = {}
        if gate:
            results[("asan", "rewrite")] = one("asan", "rewrite", name, meta, bundle)
            ok = results[("asan", "rewrite")][1] == "DETECTED"
        for tool in tools:
            for arm in a.arms:
                if (tool, arm) not in results:
                    if gate and not ok:
                        results[(tool, arm)] = (f"{name}-{tool}-{arm}", "UNSUPPORTED",
                                                "asan/rewrite gate: " + results[("asan", "rewrite")][2], 0, 0.0)
                    else:
                        results[(tool, arm)] = one(tool, arm, name, meta, bundle)
                stem, v, n, code, secs = results[(tool, arm)]
                if not gate:
                    n = (n + "; " if n else "") + "no asan/rewrite gate this run"
                rows.append(dict(bundle=bundle.name, tool=tool, arm=arm, case=name, **{"class": meta["class"]},
                                 access=meta["access"], layer=meta["layer_by_arm"][arm], verdict=v, note=n,
                                 exit_code=code, seconds=f"{secs:.2f}", stdout=stem + ".stdout", stderr=stem + ".stderr"))
                print(f"{tool:9s} {arm:8s} {name:34s} {v:15s} {n}")
    with open(bundle / "real.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    if refused:
        print(f"REFUSED (positive control not detected): {refused}", file=sys.stderr)
        sys.exit(75)


if __name__ == "__main__":
    main()
