#!/usr/bin/env python3
"""Generate the report's LaTeX tables and plot data from the committed results.

    python3 report/scripts/gen.py          (run from anywhere; writes report/tables/*.tex, *.dat)

Inputs are only committed files: the formal detection bundles listed below and the benchmark
summaries in report/tables/*.csv (made by benchmarks/plot.py). Outputs are never hand-edited.
"""
import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "report" / "tables"
LAB = [ROOT / "results" / f"2026-11-13-lab-{s}" for s in ("core", "memsys5", "lookaside", "rewrite")]
HW = ROOT / "results" / "2026-11-13-lima-hwasan"
REAL = ROOT / "results" / "2026-11-16-lab-real"
TOOLS = ["asan", "valgrind", "hwasan"]
TOOL_NAME = {"asan": "ASan", "valgrind": "Memcheck", "hwasan": "HWASan"}
CASE_NAME = {0: "overflow, write +1", 1: "overflow, read +1", 2: "overflow into slack",
             3: "overflow into live obj.", 4: "read past the pool", 5: "underflow, write -1",
             6: "underflow, read -1", 7: "underflow into header", 8: "UAF write", 9: "UAF read",
             10: "UAF after reuse", 11: "UAF after realloc", 12: "UAF after pool destroy",
             13: "double free", 14: "interior free", 15: "double free after reuse"}
CELL = {"DETECTED": r"\cD", "MISSED": r"\cM", "UNSUPPORTED": r"\cU"}


def load():
    bug, ctl = {}, Counter()
    for b in LAB + [HW]:
        for r in csv.DictReader(open(b / "matrix.csv")):
            arm = r["alloc"] + ("+annot" if r["annot"] == "1" else "")
            if r["image"] == "control":
                ctl[(r["tool"], arm, r["verdict"])] += 1
                continue
            bug[(int(r["case"]), r["tool"], arm)] = (r["verdict"], r["note"])
    return bug, ctl


def cell(v):
    verdict, note = v
    if verdict == "MISSED" and note.startswith("crashed"):
        return r"\cMs"
    return CELL[verdict]


def tally(bug, tool, arm):
    vs = [bug[(c, tool, arm)][0] for c in range(16) if (c, tool, arm) in bug]
    if not vs:
        return None
    eligible = [v for v in vs if v != "UNSUPPORTED"]
    return sum(v == "DETECTED" for v in eligible), len(eligible)


def frac(t):
    return "--" if t is None else f"{t[0]}/{t[1]}"


def summary(bug, ctl):
    layers = [("malloc baseline", "malloc", None), ("Arena (ours)", "arena", "arena+annot"),
              ("Free list (ours)", "freelist", "freelist+annot"),
              ("SQLite memsys5", "memsys5", "memsys5+annot"), ("SQLite lookaside", "lookaside", None),
              ("Arena rewrite", "arena-rewrite", None), ("Free list rewrite", "freelist-rewrite", None)]
    lines = [r"\begin{tabular}{l*{3}{cc}}", r"\toprule",
             r" & \multicolumn{2}{c}{ASan} & \multicolumn{2}{c}{Memcheck} & \multicolumn{2}{c}{HWASan} \\",
             r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
             r"allocator layer & plain & annotated & plain & annotated & plain & annotated \\", r"\midrule"]
    dat = ["tool layer plain annotated"]  # rows: tool layer plain% annotated%
    for label, plain, annot in layers:
        row = [label]
        for tool in TOOLS:
            p = tally(bug, tool, plain)
            a = tally(bug, tool, annot) if annot else None
            row += [frac(p), frac(a) if annot else ("--" if p is None else "n/a")]
            if p is not None and plain not in ("arena-rewrite",):
                name = {"freelist-rewrite": "rewrite"}.get(plain, plain)
                pv = 100 * p[0] / p[1]
                av = (100 * a[0] / a[1]) if a else "nan"
                dat.append(f"{tool} {name} {pv:.1f} {av if a is None else f'{av:.1f}'}")
        lines.append(" & ".join(row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "detect-summary.tex").write_text("\n".join(lines) + "\n")
    for tool in TOOLS:   # one file per tool, read by the pgfplots figure
        body = [l.split(" ", 1)[1] for l in dat[1:] if l.startswith(tool + " ")]
        (OUT / f"detect-{tool}.dat").write_text("layer plain annotated\n" + "\n".join(body) + "\n")
    clean = sum(n for (t, a, v), n in ctl.items() if v == "CLEAN")
    total = sum(ctl.values())
    return clean, total


def by_class(bug):
    """Detected / eligible per bug class, pooled over Arena and Free list (the layers all three
    tools ran with and without annotation); memsys5 has the same per-case verdicts as Free list."""
    classes = [("overflow (0--4)", range(0, 5)), ("underflow (5--7)", range(5, 8)),
               ("use after free (8--12)", range(8, 13)), ("invalid / double free (13--15)", range(13, 16))]
    groups = [["malloc"], ["arena", "freelist"], ["arena+annot", "freelist+annot"]]
    lines = [r"\begin{tabular}{l*{3}{ccc}}", r"\toprule",
             r" & \multicolumn{3}{c}{ASan} & \multicolumn{3}{c}{Memcheck} & \multicolumn{3}{c}{HWASan} \\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}",
             r"bug class & \code{malloc} & CMA & CMA+A & \code{malloc} & CMA & CMA+A & \code{malloc} & CMA & CMA+A \\",
             r"\midrule"]
    for label, cases in classes:
        row = [label]
        for tool in TOOLS:
            for arms in groups:
                vs = [bug[(c, tool, a)][0] for c in cases for a in arms if (c, tool, a) in bug]
                el = [v for v in vs if v != "UNSUPPORTED"]
                row.append(f"{sum(v == 'DETECTED' for v in el)}/{len(el)}")
        lines.append(" & ".join(row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "detect-class.tex").write_text("\n".join(lines) + "\n")


def real():
    """The four real SQLite bugs (corpus/real) on the lab server. Marks: dagger = the tool's report is
    an invalid access immediately before the process died of a signal; double dagger = an over-read
    reported outside the rewrite, i.e. after it left its container (arena or page-cache bulk block)."""
    rows = list(csv.DictReader(open(REAL / "real.csv")))
    desc = {"03": "use after free: connection read after close", "19": "use after free: stale R-tree node",
            "29": "over-read of a page (\\code{sqlite3Get4byte})", "31": "over-read of a page (\\code{statDecodePage})"}
    lines = [r"\begin{tabular}{rl*{6}{c}}", r"\toprule",
             r" & & \multicolumn{3}{c}{ASan} & \multicolumn{3}{c}{Memcheck} \\",
             r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
             r"\# & bug & memsys5 & shipped & rewrite & memsys5 & shipped & rewrite \\", r"\midrule"]
    for case in sorted({r["case"] for r in rows}):
        row = [case[:2], desc[case[:2]]]
        for tool in ("asan", "valgrind"):
            for arm in ("memsys5", "default", "rewrite"):
                r = next(x for x in rows if x["case"] == case and x["tool"] == tool and x["arm"] == arm)
                c = cell((r["verdict"], r["note"]))
                if r["verdict"] == "DETECTED" and int(r["exit_code"]) < 0:
                    c += r"$^{\dagger}$"
                elif r["verdict"] == "DETECTED" and r["class"] == "heap-overflow" and arm != "rewrite":
                    c += r"$^{\ddagger}$"
                row.append(c)
        lines.append(" & ".join(row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "real.tex").write_text("\n".join(lines) + "\n")


def matrix(bug, tools, arms, labels, name):
    ncol = len(arms)
    spec = "r l" + "".join("|" + "c" * ncol for _ in tools)
    lines = [r"\begin{tabular}{" + spec + "}", r"\toprule",
             r" & & " + " & ".join(rf"\multicolumn{{{ncol}}}{{c}}{{{TOOL_NAME[t]}}}" for t in tools) + r" \\",
             r" & case & " + " & ".join(labels for _ in tools) + r" \\", r"\midrule"]
    for c in range(16):
        cells = []
        for t in tools:
            for a in arms:
                cells.append(cell(bug[(c, t, a)]) if (c, t, a) in bug else r"\cNA")
        lines.append(f"{c} & {CASE_NAME[c]} & " + " & ".join(cells) + r" \\")
    lines.append(r"\midrule")
    det = []
    for t in tools:
        for a in arms:
            x = tally(bug, t, a)
            det.append(r"\scriptsize " + (frac(x) if x else "--"))
    lines.append(r" & detected / eligible & " + " & ".join(det) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / name).write_text("\n".join(lines) + "\n")


def perf():
    def rows(f):
        return list(csv.DictReader(open(OUT / f)))
    stats = {}
    evidence = []
    for source in ("benchmark-summary.csv", "lua-summary.csv", "part-b-churn-summary.csv"):
        for s in rows(source):
            key = tuple(s[k] for k in ("bundle", "benchmark", "config", "annot", "tool"))
            bundle = ROOT / "results" / s["bundle"]
            with (bundle / "benchmark.csv").open() as stream:
                raw = [r for r in csv.DictReader(stream)
                       if tuple(r[k] for k in ("bundle", "benchmark", "config", "annot", "tool")) == key]
            if sorted(int(r["run"]) for r in raw) != [1, 2, 3, 4, 5]:
                raise ValueError(f"{key}: expected exactly runs 1 through 5")
            times, rss = [], []
            for r in raw:
                t, m = float(r["seconds"]), float(r["peak_rss_kb"])
                if not all(math.isfinite(v) and v > 0 for v in (t, m)):
                    raise ValueError(f"{key}: invalid measurement")
                stem = (f"{r['config']}-{r['tool']}-a{r['annot']}-{r['run']}"
                        if r["benchmark"] == "allocator-churn" else f"{r['tool']}-{r['run']}")
                wall, peak = (bundle / f"{stem}.time").read_text().strip().split(",")
                stdout = (bundle / f"{stem}.stdout").read_text()
                recorded = (re.search(r"elapsed_seconds=([0-9.]+)", stdout).group(1)
                            if r["benchmark"] == "allocator-churn" else wall)
                if abs(float(recorded) - t) > 1e-7 or float(peak) != m:
                    raise ValueError(f"{key}: CSV differs from raw log {stem}")
                if (bundle / f"{stem}.exit").read_text().strip() != "0":
                    raise ValueError(f"{key}: failed run {stem}")
                if r["benchmark"] == "lua" and "rounds=20 objects=100000 checksum=6666766818777900" not in stdout:
                    raise ValueError(f"{key}: Lua checksum differs in {stem}")
                times.append(t)
                rss.append(m / 1024)
            values = dict(runs=5, median_seconds=median(times), min_seconds=min(times), max_seconds=max(times),
                          median_rss_mib=median(rss), min_rss_mib=min(rss), max_rss_mib=max(rss))
            for field in ("median_seconds", "median_rss_mib"):
                if abs(values[field] - float(s[field])) > 1e-6:
                    raise ValueError(f"{key}: summary {field} differs from raw measurements")
            stats[key] = values
            evidence.append(dict(zip(("bundle", "benchmark", "config", "annot", "tool"), key), **values))
    for s in evidence:
        baseline = stats[(s["bundle"], s["benchmark"], s["config"], s["annot"], "none")]
        s["time_ratio"] = s["median_seconds"] / baseline["median_seconds"]
        s["rss_ratio"] = s["median_rss_mib"] / baseline["median_rss_mib"]
    for source in ("benchmark-summary.csv", "lua-summary.csv", "part-b-churn-summary.csv"):
        for s in rows(source):
            baseline = stats[(s["bundle"], s["benchmark"], s["config"], s["annot"], "none")]
            values = stats[tuple(s[k] for k in ("bundle", "benchmark", "config", "annot", "tool"))]
            for field, metric in (("time_ratio", "median_seconds"), ("rss_ratio", "median_rss_mib")):
                if abs(float(s[field]) - values[metric] / baseline[metric]) > 1e-6:
                    raise ValueError(f"{source}: {field} differs from raw measurements")
    with (OUT / "perf-variability.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(evidence[0]))
        writer.writeheader()
        writer.writerows(evidence)
    print(f"Performance: {sum(s['runs'] for s in evidence)} raw runs checked; {len(evidence)} groups; medians, ratios, exits and logs agree")

    def value(s, metric, digits):
        v = stats[tuple(s[k] for k in ("bundle", "benchmark", "config", "annot", "tool"))]
        suffix = "seconds" if metric == "time" else "rss_mib"
        return (r"\shortstack{" + f"{v['median_' + suffix]:.{digits}f}" + r"\\{\scriptsize[" +
                f"{v['min_' + suffix]:.{digits}f}, {v['max_' + suffix]:.{digits}f}" + r"]}}")

    name = {"none": "baseline", "asan": "ASan", "valgrind": "Memcheck"}
    order = {"none": 0, "asan": 1, "valgrind": 2}
    lines = [r"\begin{tabular}{llrrrr}", r"\toprule",
             r"workload & tool & time (s) & $\times$ & peak RSS (MiB) & $\times$ \\", r"\midrule"]
    groups = [("SQLite speedtest1, default", "benchmark-summary.csv", "sqlite-default"),
              ("SQLite speedtest1, memsys5", "benchmark-summary.csv", "memsys5-256MiB-min64"),
              ("Lua 5.4.9 table/GC workload", "lua-summary.csv", "lua-default")]
    for gi, (label, f, cfg) in enumerate(groups):
        rs = sorted((r for r in rows(f) if r["config"] == cfg), key=lambda r: order[r["tool"]])
        for i, r in enumerate(rs):
            lines.append(" & ".join([label if i == 0 else "", name[r["tool"]],
                                     value(r, "time", 2), f"{float(r['time_ratio']):.2f}",
                                     value(r, "rss", 1), f"{float(r['rss_ratio']):.2f}"]) + r" \\[3pt]")
        if gi < len(groups) - 1:
            lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "perf-tools.tex").write_text("\n".join(lines) + "\n")

    churn = {(r["config"], r["annot"], r["tool"]): r for r in rows("part-b-churn-summary.csv")}
    lines = [r"\begin{tabular}{llrrrrr}", r"\toprule",
             r"allocator & tool & off (s) & on (s) & on/off & RSS off / on (MiB) & rewrite (s, MiB) \\", r"\midrule"]
    for alloc, label in (("arena", "Arena"), ("freelist", "Free list")):
        for tool in ("asan", "valgrind"):
            off, on = churn[(alloc, "0", tool)], churn[(alloc, "1", tool)]
            rw = churn[(alloc + "-rewrite", "0", tool)]
            t0, t1 = float(off["median_seconds"]), float(on["median_seconds"])
            lines.append(" & ".join([label if tool == "asan" else "", name[tool], value(off, "time", 3), value(on, "time", 3),
                                     f"{t1 / t0:.2f}$\\times$",
                                     f"{float(off['median_rss_mib']):.1f} / {float(on['median_rss_mib']):.1f}",
                                     f"{float(rw['median_seconds']):.3f}, {float(rw['median_rss_mib']):.0f}"]) + r" \\[3pt]")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "perf-churn.tex").write_text("\n".join(lines) + "\n")


def main():
    bug, ctl = load()
    clean, total = summary(bug, ctl)
    by_class(bug)
    matrix(bug, TOOLS, ["malloc", "arena", "arena+annot", "freelist", "freelist+annot"],
           r"\rot{malloc} & \rot{Arena} & \rot{Arena+A} & \rot{Free list} & \rot{Free list+A}", "matrix-core.tex")
    matrix(bug, ["asan", "valgrind"], ["memsys5", "memsys5+annot", "lookaside", "arena-rewrite", "freelist-rewrite"],
           r"\rot{memsys5} & \rot{memsys5+A} & \rot{lookaside} & \rot{Arena rewr.} & \rot{Free-list rewr.}",
           "matrix-sqlite.tex")
    perf()
    real()
    v = Counter(x[0] for x in bug.values())
    print(f"bug cells {len(bug)} {dict(v)}; controls CLEAN {clean}/{total}")


if __name__ == "__main__":
    main()
