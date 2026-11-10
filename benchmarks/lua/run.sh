#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
WORK="$ROOT/build/lua"
OUT="$(mktemp -d "$ROOT/results/$(date +%F)-lua-XXXXXX")"
BUNDLE="$(basename "$OUT")"
EXPECTED="rounds=20 objects=100000 checksum=6666766818777900"

{
  bash "$ROOT/tools/env.sh"
  /usr/bin/time --version
  "$WORK/bin/lua-baseline" -v
  "$WORK/bin/lua-asan" -v
  printf '%s\n' \
    'Lua source: https://www.lua.org/ftp/lua-5.4.9.tar.gz' \
    'Common flags: -O2 -g -fno-omit-frame-pointer' \
    'ASan additional compile/link flags: -fsanitize=address' \
    'Lua make target: linux; CC=clang' \
    'Configuration: original Lua allocator, no custom annotations' \
    'Workload: benchmarks/lua/workload.lua 20 100000' \
    'Valgrind: --tool=memcheck --leak-check=full --error-exitcode=99'
  printf 'Expected stdout: %s\n' "$EXPECTED"
  printf 'ASAN_OPTIONS=%s\n' "${ASAN_OPTIONS-<unset>}"
  printf 'LSAN_OPTIONS=%s\n' "${LSAN_OPTIONS-<unset>}"
  sha256sum "$WORK/lua-5.4.9.tar.gz" benchmarks/lua/workload.lua \
    "$WORK/bin/lua-baseline" "$WORK/bin/lua-asan"
} > "$OUT/env.txt" 2>&1

printf '%s\n' \
  'bundle,benchmark,config,tool,annot,run,seconds,peak_rss_kb' \
  > "$OUT/benchmark.csv"

for run in 1 2 3 4 5; do
  for tool in none asan valgrind; do
    case "$tool" in
      none) cmd=("$WORK/bin/lua-baseline") ;;
      asan) cmd=("$WORK/bin/lua-asan") ;;
      valgrind)
        cmd=(valgrind --tool=memcheck --leak-check=full --error-exitcode=99
             "$WORK/bin/lua-baseline")
        ;;
    esac
    stem="$OUT/$tool-$run"
    printf 'Running %s, repetition %s/5\n' "$tool" "$run"
    status=0
    /usr/bin/time -f '%e,%M' -o "$stem.time" \
      "${cmd[@]}" benchmarks/lua/workload.lua 20 100000 \
      > "$stem.stdout" 2> "$stem.stderr" || status=$?
    printf '%s\n' "$status" > "$stem.exit"
    if [[ "$status" -ne 0 ]]; then
      echo "Run failed (exit $status). Check $stem.stderr" >&2
      exit "$status"
    fi
    if [[ "$(cat "$stem.stdout")" != "$EXPECTED" ]]; then
      echo "Workload output mismatch. Check $stem.stdout" >&2
      exit 1
    fi
    IFS=, read -r seconds rss < "$stem.time"
    printf '%s,lua,lua-default,%s,0,%s,%s,%s\n' \
      "$BUNDLE" "$tool" "$run" "$seconds" "$rss" >> "$OUT/benchmark.csv"
  done
done

printf '\nResults saved to %s\n' "$OUT"
cat "$OUT/benchmark.csv"
