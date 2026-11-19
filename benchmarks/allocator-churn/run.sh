#!/usr/bin/env bash
# Linux runner; writes the shared benchmark CSV schema.
set -euo pipefail
export LC_ALL=C
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
RUNS="${ST_RUNS:-5}"
CYCLES="${ST_CYCLES:-10000}"
read -r -a TOOLS <<< "${ST_TOOLS:-none asan valgrind}"
read -r -a ALLOCS <<< "${ST_ALLOCS:-arena freelist arena-rewrite freelist-rewrite}"
prefix="${ST_SCRATCH:+scratch-}$(date +%F)-allocator-churn-XXXXXX"
OUT="$(mktemp -d "$ROOT/results/$prefix")"
BUNDLE="$(basename "$OUT")"
mkdir -p build/allocator-churn
asan_cc="${ST_ASAN_CC:-clang}"
if ! command -v "$asan_cc" >/dev/null 2>&1; then asan_cc=gcc; fi

{
  bash tools/env.sh
  printf 'workload: %s cycles, 128 allocations then 64 frees and reuses per cycle\n' "$CYCLES"
  printf 'build: -O2 -g -fno-omit-frame-pointer; ST_ANNOT=0 or 1\n'
  printf 'asan compiler: %s\n' "$asan_cc"
} > "$OUT/env.txt"
printf '%s\n' 'bundle,benchmark,config,tool,annot,run,seconds,peak_rss_kb' > "$OUT/benchmark.csv"

for alloc in "${ALLOCS[@]}"; do
  annots=(0 1)
  if [[ "$alloc" == *-rewrite ]]; then annots=(0); fi
  for annot in "${annots[@]}"; do
    for tool in "${TOOLS[@]}"; do
      if [[ "$alloc" == *-rewrite ]]; then
        src="allocators/${alloc%-rewrite}/rewrite/$alloc.c"
      else
        src="allocators/$alloc/$alloc.c"
      fi
      exe="build/allocator-churn/$alloc-$tool-a$annot"
      flags=(-O2 -g -fno-omit-frame-pointer -Icorpus/include -Iallocators/annotations "-DST_ANNOT=$annot")
      case "$tool" in
        none) cc "${flags[@]}" benchmarks/allocator-churn/churn.c "$src" -o "$exe" ;;
        asan) "$asan_cc" "${flags[@]}" -fsanitize=address -DST_TOOL_ASAN \
                    benchmarks/allocator-churn/churn.c "$src" -o "$exe" ;;
        valgrind) gcc "${flags[@]}" -DST_TOOL_VALGRIND \
                       benchmarks/allocator-churn/churn.c "$src" -o "$exe" ;;
        *) echo "unknown tool: $tool" >&2; exit 2 ;;
      esac
      for run in $(seq 1 "$RUNS"); do
        stem="$OUT/$alloc-$tool-a$annot-$run"
        cmd=("$exe" "$CYCLES")
        if [ "$tool" = valgrind ]; then
          cmd=(valgrind --tool=memcheck --leak-check=no --error-exitcode=99 "${cmd[@]}")
        fi
        status=0
        /usr/bin/time -f '%e,%M' -o "$stem.time" "${cmd[@]}" \
          > "$stem.stdout" 2> "$stem.stderr" || status=$?
        printf '%s\n' "$status" > "$stem.exit"
        if [ "$status" -ne 0 ]; then
          echo "failed: $stem (exit $status)" >&2
          exit "$status"
        fi
        IFS=, read -r wall_seconds rss < "$stem.time"
        seconds="$(sed -n 's/.*elapsed_seconds=\([0-9.]*\).*/\1/p' "$stem.stdout")"
        if [ -z "$seconds" ]; then echo "missing elapsed_seconds: $stem" >&2; exit 1; fi
        printf '%s,allocator-churn,%s,%s,%s,%s,%s,%s\n' \
          "$BUNDLE" "$alloc" "$tool" "$annot" "$run" "$seconds" "$rss" >> "$OUT/benchmark.csv"
      done
    done
  done
done
echo "results: $OUT"
