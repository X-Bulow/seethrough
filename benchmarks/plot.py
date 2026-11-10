#!/usr/bin/env python3
"""Plot five-run benchmark medians from results bundles (C5.6)."""

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
TOOLS = {"none": "Baseline", "asan": "ASan", "valgrind": "Valgrind"}
COLORS = ["#276FBF", "#E39C35", "#37866C", "#8A64AD", "#B95369", "#737C3F"]


def summarize(paths):
    groups = defaultdict(list)
    required = {"bundle", "benchmark", "config", "tool", "annot", "run",
                "seconds", "peak_rss_kb"}
    for path in paths:
        with path.open(newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"{path}: missing benchmark CSV columns")
            for line, row in enumerate(reader, 2):
                try:
                    seconds = float(row["seconds"])
                    rss = float(row["peak_rss_kb"])
                    run = int(row["run"])
                    if not all(math.isfinite(v) and v > 0 for v in (seconds, rss)):
                        raise ValueError("time and RSS must be positive finite numbers")
                    key = tuple(row[k] for k in
                                ("bundle", "benchmark", "config", "annot", "tool"))
                    groups[key].append((run, seconds, rss))
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"{path}:{line}: {exc}") from exc

    if not groups:
        raise ValueError("no benchmark rows found")
    if len({key[1] for key in groups}) != 1:
        raise ValueError("plot one benchmark at a time; pass its CSV paths explicitly")

    summaries = {}
    for key, runs in sorted(groups.items()):
        if sorted(run[0] for run in runs) != [1, 2, 3, 4, 5]:
            raise ValueError(f"{key}: expected exactly runs 1 through 5")
        summaries[key] = {
            "seconds": median(run[1] for run in runs),
            "rss_mib": median(run[2] for run in runs) / 1024,
        }
    for key, values in summaries.items():
        baseline = summaries.get((*key[:4], "none"))
        if baseline is None:
            raise ValueError(f"{key}: missing baseline in the same bundle/config/annotation")
        values["time_ratio"] = values["seconds"] / baseline["seconds"]
        values["rss_ratio"] = values["rss_mib"] / baseline["rss_mib"]
    return summaries


def plot(summaries, output, normalized, environment_label):
    series = sorted({key[:4] for key in summaries})
    tools = sorted({key[4] for key in summaries},
                   key=lambda tool: (list(TOOLS).index(tool) if tool in TOOLS else 99, tool))
    metrics = (("time_ratio", "Runtime / baseline", "rss_ratio", "Peak RSS / baseline")
               if normalized else ("seconds", "Wall time (s)", "rss_mib", "Peak RSS (MiB)"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    width = 0.8 / len(series)
    for ax, metric, ylabel in zip(axes, metrics[::2], metrics[1::2]):
        for index, identity in enumerate(series):
            config = {"sqlite-default": "Default",
                      "memsys5-256MiB-min64": "memsys5 (256 MiB)"}.get(identity[2], identity[2])
            label = config + (f", annot={identity[3]}" if identity[3] != "0" else "")
            if sum(item[2:] == identity[2:] for item in series) > 1:
                label += f" [{identity[0]}]"
            positions, values = [], []
            for position, tool in enumerate(tools):
                key = (*identity, tool)
                if key in summaries:
                    positions.append(position - 0.4 + width * (index + 0.5))
                    values.append(summaries[key][metric])
            bars = ax.bar(positions, values, width=width * 0.9, label=label,
                          color=COLORS[index % len(COLORS)])
            suffix = "x" if normalized else ""
            if len(series) <= 4:
                ax.bar_label(bars, labels=[f"{value:.2f}{suffix}" for value in values],
                             padding=3, fontsize=9)
        ax.set_xticks(range(len(tools)), [TOOLS.get(tool, tool) for tool in tools])
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.18)
        ax.yaxis.grid(True, alpha=0.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        if normalized:
            ax.axhline(1, color="#555555", linewidth=0.8, linestyle="--")
    axes[0].legend(frameon=False, fontsize=9)
    benchmark = next(iter(summaries))[1]
    title = "overhead" if normalized else "runtime and memory"
    annotation = ("no custom annotations" if all(key[3] == "0" for key in summaries)
                  else "annotation settings shown in legend")
    fig.suptitle(f"{benchmark}: {title}\nMedian of 5 runs; {annotation}", fontsize=12)
    fig.supxlabel("Ratios use each configuration's baseline. Valgrind RSS includes tool memory."
                  if normalized else f"{environment_label}. Valgrind RSS includes tool memory.",
                  fontsize=9)
    stem = output / ("benchmark-overhead" if normalized else "benchmark-performance")
    for extension in ("png", "pdf"):
        path = stem.with_suffix(f".{extension}")
        fig.savefig(path, dpi=200)
        print(path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="*", type=Path,
                        help="CSV paths (default: results/*/benchmark.csv)")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "report/figures")
    parser.add_argument("--summary", type=Path, default=ROOT / "report/tables/benchmark-summary.csv")
    parser.add_argument("--environment-label", default="VirtualBox Ubuntu x86-64 lab setup",
                        help="Machine caption for the absolute performance figure")
    args = parser.parse_args()
    paths = args.csv or sorted((ROOT / "results").glob("*/benchmark.csv"))
    if not paths:
        parser.error("no benchmark CSVs found")
    try:
        summaries = summarize(paths)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    with args.summary.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(["bundle", "benchmark", "config", "annot", "tool", "runs",
                         "median_seconds", "median_rss_mib", "time_ratio", "rss_ratio"])
        for key, values in summaries.items():
            writer.writerow([*key, 5, *(f"{values[field]:.6f}" for field in
                                       ("seconds", "rss_mib", "time_ratio", "rss_ratio"))])
    print(args.summary)
    plot(summaries, args.out_dir, normalized=False,
         environment_label=args.environment_label)
    plot(summaries, args.out_dir, normalized=True,
         environment_label=args.environment_label)


if __name__ == "__main__":
    main()
