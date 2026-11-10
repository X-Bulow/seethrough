#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$ROOT/build/sqlite-speedtest1"
mkdir -p "$WORK/bin"

for config in default memsys5; do
  flags=()
  prefix=speedtest1
  if [ "$config" = memsys5 ]; then
    flags=(-DSQLITE_ENABLE_MEMSYS5)
    prefix=speedtest1-memsys5
  fi
  for tool in baseline asan; do
    sanitizer=()
    if [ "$tool" = asan ]; then
      sanitizer=(-fsanitize=address)
    fi
    clang -O2 -g -fno-omit-frame-pointer \
      "${flags[@]}" "${sanitizer[@]}" -I"$WORK/src" \
      "$WORK/src/speedtest1.c" "$WORK/src/sqlite3.c" \
      -o "$WORK/bin/$prefix-$tool" -lm -ldl -pthread
  done
done
