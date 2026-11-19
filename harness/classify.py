#!/usr/bin/env python3
"""Classify detector output using execution markers and report signatures.

Reports before READY are TOOL-ERROR. Signal-handler crashes after READY count
as MISSED, not defect detection. Callers handle controls and preconditions.
"""
import re

CRASH = re.compile(r"(SEGV|BUS|FPE|ILL|ABRT|TRAP)\b")
REPORT = {
    "asan":     re.compile(r"ERROR: AddressSanitizer: (\S+)"),
    "hwasan":   re.compile(r"ERROR: HWAddressSanitizer: (\S+)"),
    "ubsan":    re.compile(r"runtime error: (.+)"),
    "valgrind": re.compile(r"(Invalid (read|write) of size \d+|Invalid free\(\)|Mismatched free)"),
    "lowfat":   re.compile(r"LOWFAT ERROR: (.+)"),
}


def classify(tool, stdout, stderr, exit_code):
    reached = "ST READY" in stdout
    done = "ST DONE" in stdout
    # tool "none" is the plain run: it only tells reached / completed / crashed
    m = None if tool == "none" else (REPORT[tool].search(stderr) or REPORT[tool].search(stdout))
    if m and CRASH.match(m.group(1)):
        # A sanitizer signal-handler report is a crash, not a defect diagnosis.
        return ("MISSED" if reached else "TOOL-ERROR"), f"crashed {m.group(1)} (tool signal handler, not a detection)"
    if m:
        return ("DETECTED" if reached else "TOOL-ERROR"), m.group(1)
    if done and exit_code == 0:
        return "MISSED", ""
    if reached:
        # Reached the defect but crashed without a detector report.
        return "MISSED", f"crashed exit={exit_code}"
    return "TOOL-ERROR", f"never reached READY exit={exit_code}"


if __name__ == "__main__":
    import sys, json
    tool, out, err, code = sys.argv[1], open(sys.argv[2]).read(), open(sys.argv[3]).read(), int(sys.argv[4])
    v, note = classify(tool, out, err, code)
    print(json.dumps({"verdict": v, "note": note}))
