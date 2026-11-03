#!/usr/bin/env python3
"""Build and run every cell of the matrix, write results/<bundle>/matrix.csv.

    run-matrix.py --tools asan valgrind --allocs malloc arena --annots 0 1 \
                  --cases all --out results/2026-11-05-server

For every tool: first the positive controls (corpus/controls/*.c, plain malloc). If either is
not DETECTED the tool gets no verdicts this run and the script exits 75 (the Capstone corpus
convention: an infrastructure failure can never be read as a measurement).

Then for every (tool, alloc, annot, case): build the bug image and the control image via
`make image ...`, run each under the tool with a timeout, classify, and append a row. The raw
stdout/stderr of every run is kept beside the CSV, named like the row, so a verdict can be
re-read without re-running.

TODO(A4.1): the build and run commands below are the contract with Makefile and tools/flags.mk;
fill in as those land. Nothing here is specific to the lab server except the assumption that
the tools are on PATH (tools/setup-server.sh).
"""
import argparse, csv, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
from classify import classify  # noqa: E402

COLUMNS = ["bundle", "tool", "alloc", "annot", "case", "class", "access", "image",
           "verdict", "note", "exit_code", "seconds", "stdout", "stderr"]
TIMEOUT = 60


def cases(selection):
    index = ROOT / "corpus" / "cases"
    dirs = sorted(d for d in index.iterdir() if (d / "case.json").exists())
    if selection != ["all"]:
        dirs = [d for d in dirs if d.name in selection]
    return [(d.name, json.loads((d / "case.json").read_text())) for d in dirs]


def build(tool, alloc, annot, case_dir, control, out):
    cmd = ["make", "-s", "-C", str(ROOT), "image", f"TOOL={tool}", f"ALLOC={alloc}",
           f"ANNOT={annot}", f"CASE={case_dir}", f"CONTROL={int(control)}", f"OUT={out}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr


def run(tool, exe):
    """Run one image under its tool. Valgrind wraps the binary; sanitizers are in the binary."""
    cmd = [str(exe)]
    if tool == "valgrind":
        cmd = ["valgrind", "--error-exitcode=99", "--leak-check=no", str(exe)]
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:abort_on_error=0",
               HWASAN_OPTIONS="abort_on_error=0", UBSAN_OPTIONS="print_stacktrace=1")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, env=env)
        return r.stdout, r.stderr, r.returncode, time.time() - t0
    except subprocess.TimeoutExpired as e:
        return (e.stdout or ""), (e.stderr or "") + "\nST TIMEOUT", -1, time.time() - t0


def positive_controls(tool, bundle):
    ok = True
    for src in sorted((ROOT / "corpus" / "controls").glob("*.c")):
        exe = ROOT / "build" / bundle.name / f"control-{tool}-{src.stem}"
        exe.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["make", "-s", "-C", str(ROOT), "control-image", f"TOOL={tool}", f"SRC={src}", f"OUT={exe}"]
        if subprocess.run(cmd, capture_output=True).returncode != 0:
            print(f"[{tool}] positive control {src.name}: BUILD FAILED"); ok = False; continue
        out, err, code, _ = run(tool, exe)
        v, note = classify(tool, out, err, code)
        print(f"[{tool}] positive control {src.name}: {v} {note}")
        ok &= v == "DETECTED"
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", nargs="+", required=True)
    ap.add_argument("--allocs", nargs="+", default=["malloc"])
    ap.add_argument("--annots", nargs="+", type=int, default=[0])
    ap.add_argument("--cases", nargs="+", default=["all"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    bundle = Path(a.out); bundle.mkdir(parents=True, exist_ok=True)
    subprocess.run(["bash", str(ROOT / "tools" / "env.sh")], stdout=open(bundle / "env.txt", "w"))
    rows = []
    refused = []
    for tool in a.tools:
        # "none" is the uninstrumented run; it has nothing to detect the controls with
        if tool != "none" and not positive_controls(tool, bundle):
            refused.append(tool); continue
        for alloc in a.allocs:
            for annot in a.annots:
                for name, meta in cases(a.cases):
                    verdicts = {}
                    for control in (False, True):
                        image = "control" if control else "bug"
                        stem = f"{meta['case']:02d}-{name}-{tool}-{alloc}-a{annot}-{image}"
                        exe = ROOT / "build" / bundle.name / stem
                        built, log = build(tool, alloc, annot, name, control, exe)
                        if not built:
                            (bundle / (stem + ".build.log")).write_text(log)
                            verdicts[image] = ("UNSUPPORTED", "build failed", 0, 0.0); continue
                        out, err, code, secs = run(tool, exe)
                        (bundle / (stem + ".stdout")).write_text(out)
                        (bundle / (stem + ".stderr")).write_text(err)
                        v, n = classify(tool, out, err, code)
                        if control and v == "MISSED":
                            v = "CLEAN"          # a control that ran to completion unreported is what it should do
                        verdicts[image] = (v, n, code, secs)
                    # the control decides whether the bug verdict stands
                    bv, bn, bc, bs = verdicts["bug"]; cv, cn, cc, cs = verdicts["control"]
                    if cv == "DETECTED":
                        bv, bn = "FALSE-POSITIVE", f"control also reported: {cn}"
                    elif cv == "TOOL-ERROR":
                        bv, bn = "TOOL-ERROR", f"control: {cn}"
                    for image, (v, n, c, s) in (("bug", (bv, bn, bc, bs)), ("control", (cv, cn, cc, cs))):
                        rows.append(dict(bundle=bundle.name, tool=tool, alloc=alloc, annot=annot,
                                         case=meta["case"], **{"class": meta["class"]}, access=meta["access"],
                                         image=image, verdict=v, note=n, exit_code=c, seconds=f"{s:.2f}",
                                         stdout=f"{meta['case']:02d}-{name}-{tool}-{alloc}-a{annot}-{image}.stdout",
                                         stderr=f"{meta['case']:02d}-{name}-{tool}-{alloc}-a{annot}-{image}.stderr"))
                    print(f"{tool:9s} {alloc:9s} annot={annot} {name:24s} {bv:15s} {bn}")
    with open(bundle / "matrix.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    if refused:
        print(f"REFUSED (positive control not detected): {refused}", file=sys.stderr)
        sys.exit(75)


if __name__ == "__main__":
    main()
