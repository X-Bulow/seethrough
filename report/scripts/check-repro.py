#!/usr/bin/env python3
"""Reproduce report tables and figures from existing bundles in an isolated copy.

This is an artifact check, not a new execution of the C detection or benchmark programs.
Requires Python and benchmarks/requirements.txt. Keeps the copy and logs under build/.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    (ROOT / "build").mkdir(exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix="report-repro-", dir=ROOT / "build"))
    for folder in ("report/src", "report/scripts", "harness"):
        shutil.copytree(ROOT / folder, target / folder)
    for source in (ROOT / "corpus/cases").glob("case*/case.json"):
        dest = target / source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    (target / "benchmarks").mkdir()
    shutil.copy2(ROOT / "benchmarks/plot.py", target / "benchmarks/plot.py")
    shutil.copy2(ROOT / "Makefile", target / "Makefile")
    lab = [f"2026-11-13-lab-{s}" for s in ("core", "memsys5", "lookaside", "rewrite")]
    replicas = [f"2026-11-10-ec2-b-{s}" for s in ("core", "memsys5", "lookaside", "rewrite")]
    hw = "2026-11-13-lima-hwasan"
    sqlite = ["2026-11-05-sqlite-speedtest1-A3VkNv", "2026-11-05-sqlite-speedtest1-memsys5-LGSfcu"]
    lua, churn = "2026-11-08-lua-36YPxm", "2026-11-10-allocator-churn-IkUTIU"
    for bundle in lab + replicas + [hw] + sqlite + [lua, churn]:
        shutil.copytree(ROOT / "results" / bundle, target / "results" / bundle)
    (target / "report/tables").mkdir()
    print(f"Isolated artifact check: {target}", flush=True)

    def run(name, *args):
        with (target / f"{name}.log").open("w", encoding="utf-8") as log:
            subprocess.run([sys.executable, *args], cwd=target, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        print(f"PASS {name}", flush=True)

    def plot(name, bundles, output, summary, *extra):
        run(name, "benchmarks/plot.py", *(f"results/{b}/benchmark.csv" for b in bundles),
            "--out-dir", output, "--summary", f"report/tables/{summary}", *extra)

    plot("sqlite", sqlite, "report/figures", "benchmark-summary.csv")
    plot("lua", [lua], "report/figures/lua", "lua-summary.csv")
    plot("churn", [churn], "churn-figures", "part-b-churn-summary.csv",
         "--environment-label", "AWS EC2 Ubuntu 26.04 x86-64")
    for ext in ("png", "pdf"):
        shutil.copy2(target / f"churn-figures/benchmark-performance.{ext}",
                     target / f"report/figures/part-b-churn-performance.{ext}")
    run("tables", "report/scripts/gen.py")
    run("audit-lab", "harness/audit-missed.py", *(f"results/{b}" for b in lab),
        "--replica", *(f"results/{b}" for b in replicas))
    run("audit-hwasan", "harness/audit-missed.py", f"results/{hw}")
    run("expectations-lab", "harness/render-matrix.py", *(f"results/{b}" for b in lab), "--check")
    files = list((target / "report/tables").iterdir()) + list((target / "report/figures").rglob("*.png"))
    for generated in files:
        relative = generated.relative_to(target)
        if generated.read_bytes() != (ROOT / relative).read_bytes():
            raise ValueError(f"Regenerated artifact differs: {relative}")
    print(f"PASS {len(files)} tables, data files and PNG figures match the working report", flush=True)
    print("No detection or benchmark executables were rerun. Full clean-clone execution remains separate.")


if __name__ == "__main__":
    main()
