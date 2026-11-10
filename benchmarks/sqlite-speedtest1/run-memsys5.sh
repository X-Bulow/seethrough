#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
WORK="$ROOT/build/sqlite-speedtest1"
OUT="$(mktemp -d "$ROOT/results/$(date +%F)-sqlite-speedtest1-memsys5-XXXXXX")"
BUNDLE="$(basename "$OUT")"

{
  date -Is
  uname -a
  cat /etc/os-release
  lscpu
  clang --version
  valgrind --version
  /usr/bin/time --version
  git rev-parse HEAD
  git status --short
  printf '%s\n' \
    'SQLite: 3.50.4' \
    'Common flags: -O2 -g -fno-omit-frame-pointer -DSQLITE_ENABLE_MEMSYS5' \
    'ASan additional flags: -fsanitize=address' \
    'Link libraries: -lm -ldl -pthread' \
    'Workload: --memdb --size 100 --testset main --heap 268435456 64' \
    'Configuration: memsys5, 256MiB heap, minimum allocation 64 bytes, no custom annotations' \
    'Valgrind: --tool=memcheck --leak-check=full --error-exitcode=99'
  printf 'ASAN_OPTIONS=%s\n' "${ASAN_OPTIONS-<unset>}"
  printf 'LSAN_OPTIONS=%s\n' "${LSAN_OPTIONS-<unset>}"
  sha256sum "$WORK/src/"*.c "$WORK/src/sqlite3.h" \
    "$WORK/bin/speedtest1-memsys5-baseline" "$WORK/bin/speedtest1-memsys5-asan"
} > "$OUT/env.txt" 2>&1

printf '%s\n' \
  'bundle,benchmark,config,tool,annot,run,seconds,peak_rss_kb' \
  > "$OUT/benchmark.csv"

for run in 1 2 3 4 5; do
  for tool in none asan valgrind; do
    case "$tool" in
      none)
        cmd=("$WORK/bin/speedtest1-memsys5-baseline")
        ;;
      asan)
        cmd=("$WORK/bin/speedtest1-memsys5-asan")
        ;;
      valgrind)
        cmd=(valgrind --tool=memcheck --leak-check=full
             --error-exitcode=99 "$WORK/bin/speedtest1-memsys5-baseline")
        ;;
    esac

    stem="$OUT/$tool-$run"
    printf 'Running %s, repetition %s/5\n' "$tool" "$run"

    status=0
    /usr/bin/time -f '%e,%M' -o "$stem.time" \
      "${cmd[@]}" --memdb --size 100 --testset main --heap 268435456 64 \
      > "$stem.stdout" 2> "$stem.stderr" || status=$?

    printf '%s\n' "$status" > "$stem.exit"
    if [ "$status" -ne 0 ]; then
      printf 'Run failed (exit %s). Check %s.stderr\n' "$status" "$stem"
      exit "$status"
    fi

    IFS=, read -r seconds rss < "$stem.time"
    printf '%s,sqlite-speedtest1,memsys5-256MiB-min64,%s,0,%s,%s,%s\n' \
      "$BUNDLE" "$tool" "$run" "$seconds" "$rss" \
      >> "$OUT/benchmark.csv"
  done
done

printf '\nResults saved to %s\n' "$OUT"
cat "$OUT/benchmark.csv"
