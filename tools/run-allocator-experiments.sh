#!/usr/bin/env bash
# Full allocator detection and performance run on an x86-64 Ubuntu VM.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PREFIX="${1:-results/$(date +%F)-server}"
for suffix in core memsys5 lookaside rewrite; do
  if [ -e "$PREFIX-$suffix" ]; then
    echo "refusing to overwrite $PREFIX-$suffix" >&2
    exit 2
  fi
done
command -v clang >/dev/null
command -v gcc >/dev/null
command -v valgrind >/dev/null
tools/fetch-sqlite.sh 3.53.3 >/dev/null

python3 harness/run-matrix.py --tools asan valgrind \
  --allocs malloc arena freelist --annots 0 1 --cases all \
  --out "$PREFIX-core"
python3 harness/run-matrix.py --tools asan valgrind \
  --allocs memsys5 --annots 0 1 --cases all \
  --out "$PREFIX-memsys5"
python3 harness/run-matrix.py --tools asan valgrind \
  --allocs lookaside --annots 0 --cases all \
  --out "$PREFIX-lookaside"
python3 harness/run-matrix.py --tools asan valgrind \
  --allocs arena-rewrite freelist-rewrite --annots 0 --cases all \
  --out "$PREFIX-rewrite"
bash benchmarks/allocator-churn/run.sh
