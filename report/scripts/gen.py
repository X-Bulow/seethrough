#!/usr/bin/env python3
"""Generate the report's LaTeX tables and plot data from the committed results.

    python3 report/scripts/gen.py          (run from anywhere; writes report/tables/*.tex, *.dat)

Inputs are only committed files: the formal detection bundles listed below and the benchmark
summaries in report/tables/*.csv (made by benchmarks/plot.py). Outputs are never hand-edited.
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "report" / "tables"
LAB = [ROOT / "results" / f"2026-11-13-lab-{s}" for s in ("core", "memsys5", "lookaside", "rewrite")]
HW = ROOT / "results" / "2026-11-13-lima-hwasan"
TOOLS = ["asan", "valgrind", "hwasan"]
TOOL_NAME = {"asan": "ASan", "valgrind": "Valgrind", "hwasan": "HWASan"}
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
              ("Arena rewrite", "arena-rewrite", None), ("Free-list rewrite", "freelist-rewrite", None)]
    lines = [r"\begin{tabular}{l*{3}{cc}}", r"\toprule",
             r" & \multicolumn{2}{c}{ASan} & \multicolumn{2}{c}{Valgrind} & \multicolumn{2}{c}{HWASan} \\",
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
             r" & \multicolumn{3}{c}{ASan} & \multicolumn{3}{c}{Valgrind} & \multicolumn{3}{c}{HWASan} \\",
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
    name = {"none": "baseline", "asan": "ASan", "valgrind": "Valgrind"}
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
                                     f"{float(r['median_seconds']):.2f}", f"{float(r['time_ratio']):.2f}",
                                     f"{float(r['median_rss_mib']):.1f}", f"{float(r['rss_ratio']):.2f}"]) + r" \\")
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
            lines.append(" & ".join([label if tool == "asan" else "", name[tool], f"{t0:.3f}", f"{t1:.3f}",
                                     f"{t1 / t0:.2f}$\\times$",
                                     f"{float(off['median_rss_mib']):.1f} / {float(on['median_rss_mib']):.1f}",
                                     f"{float(rw['median_seconds']):.3f}, {float(rw['median_rss_mib']):.0f}"]) + r" \\")
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
    v = Counter(x[0] for x in bug.values())
    print(f"bug cells {len(bug)} {dict(v)}; controls CLEAN {clean}/{total}")


if __name__ == "__main__":
    main()
