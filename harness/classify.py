#!/usr/bin/env python3
"""Turn one run (stdout, stderr, exit code, tool) into a verdict.

    DETECTED        the tool printed a report AND the stdout shows ST READY (the defect was reached)
    MISSED          ST DONE printed, exit 0, no report
    FALSE-POSITIVE  (decided by the caller) the control image got DETECTED
    TOOL-ERROR      no ST READY, or a crash with no report, or a report before READY
    UNSUPPORTED     (decided by the caller) the build failed for this tool x allocator

Each tool's report signature is one regex. Add tools here only. TODO(A4.2): verify the
Valgrind and HWASan patterns against real output on the server before trusting them.
"""
import re

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
    if m:
        return ("DETECTED" if reached else "TOOL-ERROR"), m.group(1)
    if done and exit_code == 0:
        return "MISSED", ""
    if reached:
        # crashed after the defect with no report (e.g. SIGSEGV from a corrupted free list):
        # the tool did not see it, the hardware did. Recorded as MISSED with the signal noted.
        return "MISSED", f"crashed exit={exit_code}"
    return "TOOL-ERROR", f"never reached READY exit={exit_code}"


if __name__ == "__main__":
    import sys, json
    tool, out, err, code = sys.argv[1], open(sys.argv[2]).read(), open(sys.argv[3]).read(), int(sys.argv[4])
    v, note = classify(tool, out, err, code)
    print(json.dumps({"verdict": v, "note": note}))
