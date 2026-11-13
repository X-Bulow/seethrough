#!/usr/bin/env python3
"""Render one or more matrix.csv files as the Detection Matrix for the report.

    render-matrix.py results/2026-11-10-ec2-b-core                       # markdown to stdout
    render-matrix.py results/A results/B --tools asan valgrind --format latex --out matrix.tex
    render-matrix.py results/2026-11-10-ec2-b-core --check               # compare with case.json

Rows are cases, columns are (tool, arm). An arm is the allocator, plus "+annot" when the
annotations were on: the same names `case.json` uses under "expected" ("arena+annot").
Columns follow the order of --tools and of the arms present in the data, unless --arms is given.

Bug-row verdicts are abbreviated D / M / U / FP / TE (DETECTED, MISSED, UNSUPPORTED,
FALSE-POSITIVE, TOOL-ERROR). A MISSED whose note says the program crashed in the tool's signal
handler is shown as M*. Below the cases: how many cells were DETECTED out of those that could
be constructed (UNSUPPORTED cells are left out of the denominator), and how many controls ran
CLEAN. Every control that did not run clean is listed under the table.

A cell measured in two bundles is an error: the script never picks one silently.

--check compares every bug cell with the first word of case.json's expected[tool][arm] and
lists the cells that differ; it exits 1 if any do. Cells without an expectation are skipped.
"""
import argparse, csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOC_ORDER = ["malloc", "arena", "freelist", "memsys5", "lookaside", "arena-rewrite", "freelist-rewrite"]
ABBREV = {"DETECTED": "D", "MISSED": "M", "UNSUPPORTED": "U", "FALSE-POSITIVE": "FP", "TOOL-ERROR": "TE"}
LEGEND = ("D = DETECTED, M = MISSED, M* = MISSED, crashed in the tool's signal handler, "
          "U = UNSUPPORTED (precondition not met or build failed), FP = FALSE-POSITIVE, "
          "TE = TOOL-ERROR; +A = annotations on.")


def arm_name(alloc, annot):
    return alloc + ("+annot" if str(annot) == "1" else "")


def arm_label(arm):
    return arm.replace("+annot", "+A")


def arm_key(arm):
    alloc = arm.replace("+annot", "")
    pos = ALLOC_ORDER.index(alloc) if alloc in ALLOC_ORDER else len(ALLOC_ORDER)
    return (pos, alloc, arm.endswith("+annot"))


def load(paths):
    cells, bundles = {}, []
    for p in paths:
        p = Path(p)
        csv_path = p / "matrix.csv" if p.is_dir() else p
        if not csv_path.exists():
            sys.exit(f"{csv_path}: not found")
        for r in csv.DictReader(open(csv_path, newline="")):
            key = (r["tool"], arm_name(r["alloc"], r["annot"]), int(r["case"]), r["image"])
            if key in cells:
                sys.exit(f"{key} appears in both {cells[key]['bundle']} and {r['bundle']}")
            cells[key] = r
            if r["bundle"] not in bundles:
                bundles.append(r["bundle"])
    return cells, bundles


def case_names():
    names, expected = {}, {}
    for d in sorted((ROOT / "corpus" / "cases").iterdir()):
        if (d / "case.json").exists():
            meta = json.loads((d / "case.json").read_text())
            names[meta["case"]] = d.name.split("-", 1)[1]
            expected[meta["case"]] = meta.get("expected", {})
    return names, expected


def cell_text(r):
    if r is None:
        return ""
    v = ABBREV.get(r["verdict"], r["verdict"])
    if r["verdict"] == "MISSED" and r["note"].startswith("crashed"):
        v += "*"
    return v


def build_table(cells, tools, arms, cases, names):
    header = ["case"] + [f"{t} {arm_label(a)}" for t, a in zip(tools, arms)]
    body = []
    for c in cases:
        body.append([f"{c:02d} {names.get(c, '?')}"] +
                    [cell_text(cells.get((t, a, c, "bug"))) for t, a in zip(tools, arms)])
    detected, clean = ["detected"], ["controls clean"]
    for t, a in zip(tools, arms):
        bug = [cells[(t, a, c, "bug")] for c in cases if (t, a, c, "bug") in cells]
        ctl = [cells[(t, a, c, "control")] for c in cases if (t, a, c, "control") in cells]
        built = [r for r in bug if r["verdict"] != "UNSUPPORTED"]
        detected.append(f"{sum(r['verdict'] == 'DETECTED' for r in built)}/{len(built)}")
        clean.append(f"{sum(r['verdict'] == 'CLEAN' for r in ctl)}/{len(ctl)}")
    return header, body, [detected, clean]


def markdown(header, body, footer):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for row in body + footer:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def latex(header, body, footer, tools, arms):
    esc = lambda s: s.replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")
    groups = []                                 # (tool, span) runs of adjacent columns
    for t in tools:
        if groups and groups[-1][0] == t:
            groups[-1][1] += 1
        else:
            groups.append([t, 1])
    out = [r"\begin{tabular}{l" + "c" * len(arms) + "}", r"\toprule"]
    out.append(" & " + " & ".join(rf"\multicolumn{{{n}}}{{c}}{{{esc(t)}}}" for t, n in groups) + r" \\")
    col = 2
    rules = []
    for _, n in groups:
        rules.append(rf"\cmidrule(lr){{{col}-{col + n - 1}}}")
        col += n
    out.append("".join(rules))
    out.append("case & " + " & ".join(esc(arm_label(a)) for a in arms) + r" \\")
    out.append(r"\midrule")
    for row in body:
        out.append(" & ".join(esc(x) for x in row) + r" \\")
    out.append(r"\midrule")
    for row in footer:
        out.append(" & ".join(esc(x) for x in row) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def check(cells, tools, arms, cases, names, expected):
    diffs, compared = [], 0
    for t, a in zip(tools, arms):
        for c in cases:
            r = cells.get((t, a, c, "bug"))
            want = expected.get(c, {}).get(t, {}).get(a)
            if r is None or not want:
                continue
            compared += 1
            if want.split()[0] != r["verdict"]:
                diffs.append(f"case {c:02d} {names.get(c, '?')}  {t} {a}: expected {want!r}, "
                             f"measured {r['verdict']} {r['note']}".rstrip())
    return compared, diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bundles", nargs="+", help="bundle directories or matrix.csv files")
    ap.add_argument("--tools", nargs="+", help="tools to show, in this order (default: as found)")
    ap.add_argument("--arms", nargs="+", help="arms to show, e.g. malloc arena arena+annot (default: all found)")
    ap.add_argument("--format", choices=["md", "latex"], default="md")
    ap.add_argument("--out", help="write the table here instead of stdout")
    ap.add_argument("--check", action="store_true", help="compare bug cells with case.json expectations")
    a = ap.parse_args()

    cells, bundles = load(a.bundles)
    names, expected = case_names()
    found_tools = []
    for (t, _, _, _) in cells:
        if t not in found_tools:
            found_tools.append(t)
    tools = a.tools or found_tools
    columns = []
    for t in tools:
        present = sorted({arm for (tt, arm, _, _) in cells if tt == t}, key=arm_key)
        for arm in (a.arms or present):
            if arm in present:
                columns.append((t, arm))
    if not columns:
        sys.exit("no cells match --tools / --arms")
    col_tools, col_arms = [t for t, _ in columns], [arm for _, arm in columns]
    cases = sorted({c for (t, arm, c, _) in cells if (t, arm) in set(columns)})

    header, body, footer = build_table(cells, col_tools, col_arms, cases, names)
    dirty = [f"{t} {arm} case {c:02d}: control {r['verdict']} {r['note']}".rstrip()
             for (t, arm, c, img), r in sorted(cells.items())
             if img == "control" and (t, arm) in set(columns) and r["verdict"] != "CLEAN"]
    if a.format == "md":
        text = (markdown(header, body, footer) + "\n\n" + LEGEND + "\n\nSource: " +
                ", ".join(f"`{b}`" for b in bundles) + "\n")
        if dirty:
            text += "\nControls that did not run clean:\n" + "".join(f"- {d}\n" for d in dirty)
    else:
        text = (f"% generated by harness/render-matrix.py from {', '.join(bundles)}\n% {LEGEND}\n" +
                latex(header, body, footer, col_tools, col_arms) + "\n")
        if dirty:
            text += "".join(f"% control not clean: {d}\n" for d in dirty)
    if a.out:
        Path(a.out).write_text(text)
    else:
        sys.stdout.write(text)

    if a.check:
        compared, diffs = check(cells, col_tools, col_arms, cases, names, expected)
        print(f"\ncheck: {compared} cells compared with case.json, {len(diffs)} differ", file=sys.stderr)
        for d in diffs:
            print("  " + d, file=sys.stderr)
        if diffs:
            sys.exit(1)


if __name__ == "__main__":
    main()
