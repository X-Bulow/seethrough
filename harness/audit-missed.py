#!/usr/bin/env python3
"""A5.13: check that every MISSED / FALSE-POSITIVE in the given bundles is a real miss.

    harness/audit-missed.py BUNDLE... [--replica BUNDLE...] [--list]

For every bug row the matrix calls MISSED it checks, from the raw files the bundle keeps:
  reached   stdout has ST READY, so the defect line was executed
  finished  stdout has ST DONE and exit 0, or the row is a recorded crash after READY
  silent    stderr carries no report of any tool (a broader pattern set than classify.py's),
            except the signal-handler SEGV line of a recorded crash; no ST TIMEOUT
  memcheck  Valgrind rows end with "ERROR SUMMARY: 0 errors"
and it reports, as context, whether the same case is DETECTED by that tool on malloc (which
shows the access is instrumented and executed), what case.json predicted, and whether a
replica bundle (--replica, e.g. the EC2 run) gave the same verdict. It also checks the build
setup the verdicts rely on: -O0 detection builds, a clean tree in env.txt, CLEAN controls.

Exit 1 if any mechanical check fails; the categories of the misses are in docs/missed-review.md.
"""
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAN_REPORT = re.compile(r"ERROR: (?:HW)?AddressSanitizer: (\S+)")
OTHER_REPORT = re.compile(r"runtime error:|Invalid (read|write|free)|Mismatched free|Conditional jump|"
                          r"Source and destination overlap|uninitialised|LOWFAT ERROR|ERROR: LeakSanitizer")
CRASH = re.compile(r"(SEGV|BUS|FPE|ILL|ABRT|TRAP)\b")


def rows(bundles):
    for b in bundles:
        for r in csv.DictReader(open(Path(b) / "matrix.csv")):
            r["_dir"] = Path(b)
            r["arm"] = r["alloc"] + ("+annot" if r["annot"] == "1" else "")
            yield r


def expected():
    out = {}
    for f in (ROOT / "corpus" / "cases").glob("case*/case.json"):
        d = json.loads(f.read_text())
        for tool, arms in d["expected"].items():
            for arm, v in arms.items():
                if arm != "why":
                    out[(d["case"], tool, arm)] = v.split()[0]
    return out


def setup_checks(bundles):
    problems = []
    mk = (ROOT / "Makefile").read_text()
    if not re.search(r"^OPT\s*\?=\s*-O0 -g$", mk, re.M):
        problems.append("Makefile: detection builds are not OPT ?= -O0 -g")
    if "OPT=" in (ROOT / "harness" / "run-matrix.py").read_text():
        problems.append("run-matrix.py overrides OPT")
    for b in bundles:
        env = (Path(b) / "env.txt").read_text()
        if "dirty=0" not in env:
            problems.append(f"{b}: env.txt does not record a clean tree")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--replica", nargs="*", default=[])
    ap.add_argument("--list", action="store_true", help="print every MISSED row")
    a = ap.parse_args()

    all_rows = list(rows(a.bundles))
    bug = {(int(r["case"]), r["tool"], r["arm"]): r for r in all_rows if r["image"] == "bug"}
    replica = {(int(r["case"]), r["tool"], r["arm"]): r["verdict"] for r in rows(a.replica) if r["image"] == "bug"}
    exp = expected()
    problems = setup_checks(a.bundles)

    controls = Counter(r["verdict"] for r in all_rows if r["image"] == "control")
    if set(controls) - {"CLEAN"}:
        problems.append(f"controls not all CLEAN: {dict(controls)}")
    fp = [k for k, r in bug.items() if r["verdict"] == "FALSE-POSITIVE"]
    te = [k for k, r in bug.items() if r["verdict"] == "TOOL-ERROR"]
    if fp: problems.append(f"FALSE-POSITIVE rows: {fp}")
    if te: problems.append(f"TOOL-ERROR rows: {te}")

    missed = sorted(k for k, r in bug.items() if r["verdict"] == "MISSED")
    by_pred = Counter(); by_arm = defaultdict(Counter); listing = []
    for k in missed:
        case, tool, arm = k
        r = bug[k]
        out = (r["_dir"] / r["stdout"]).read_text()
        err = (r["_dir"] / r["stderr"]).read_text()
        crash = r["note"].startswith("crashed")
        fails = []
        if "ST READY" not in out: fails.append("not reached")
        if not crash and not ("ST DONE" in out and r["exit_code"] == "0"): fails.append("did not finish")
        if "ST TIMEOUT" in err: fails.append("timeout")
        # a recorded crash may carry the sanitizer's own signal report (SEGV ...), nothing else
        reports = [t for t in SAN_REPORT.findall(err) if not (crash and CRASH.match(t))]
        reports += [l.strip()[:80] for l in err.splitlines() if OTHER_REPORT.search(l)]
        if reports: fails.append("report in stderr: " + reports[0])
        if tool == "valgrind" and "ERROR SUMMARY: 0 errors" not in err: fails.append("memcheck error summary not 0")
        if fails:
            problems.append(f"case {case} {tool} {arm}: " + "; ".join(fails))
        # malloc has no annotation hook, so malloc+annot carries malloc's prediction
        pred = exp.get(k, exp.get((case, tool, "malloc"), "none") if arm == "malloc+annot" else "none")
        by_pred[pred] += 1
        by_arm[(tool, arm)][pred] += 1
        malloc_v = bug.get((case, tool, "malloc"), {}).get("verdict", "-")
        rep = replica.get(k, "-")
        if rep not in ("-", "MISSED"):
            problems.append(f"case {case} {tool} {arm}: replica says {rep}")
        listing.append((case, tool, arm, "crash" if crash else "silent", pred, malloc_v, rep))

    print(f"bug rows {len(bug)}; MISSED {len(missed)}; FALSE-POSITIVE {len(fp)}; TOOL-ERROR {len(te)}; "
          f"controls {dict(controls)}")
    print(f"MISSED vs case.json prediction: {dict(by_pred)}  (none = arm without a prediction)")
    for (tool, arm), c in sorted(by_arm.items()):
        print(f"  {tool:8} {arm:17} " + "  ".join(f"{p}={n}" for p, n in sorted(c.items())))
    unexpected = [l for l in listing if l[4] == "DETECTED"]
    print("MISSED where case.json predicted DETECTED:", unexpected or "none")
    if a.replica:
        same = sum(1 for k in bug if k in replica and replica[k] == bug[k]["verdict"])
        both = sum(1 for k in bug if k in replica)
        print(f"replica: {same}/{both} shared bug cells have the same verdict")
    if a.list:
        print("\ncase tool     arm               how    predicted  malloc     replica")
        for l in listing:
            print("%4d %-8s %-17s %-6s %-10s %-10s %s" % l)
    if problems:
        print("\nPROBLEMS:"); [print("  " + p) for p in problems]
        return 1
    print("\nall mechanical checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
