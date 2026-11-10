#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$ROOT/build/lua"
mkdir -p "$WORK/bin"

curl -fL https://www.lua.org/ftp/lua-5.4.9.tar.gz -o "$WORK/lua-5.4.9.tar.gz"
printf '%s  %s\n' \
  2335b6c582a52654f94612bf10d2f4672805d05329aa6568b1d8cd9e5c6fb8e6 \
  "$WORK/lua-5.4.9.tar.gz" | sha256sum -c -
tar -xzf "$WORK/lua-5.4.9.tar.gz" -C "$WORK"

for config in baseline asan; do
  cflags="-O2 -g -fno-omit-frame-pointer"
  ldflags=""
  if [[ "$config" == asan ]]; then
    cflags+=" -fsanitize=address"
    ldflags="-fsanitize=address"
  fi
  # Clean between configurations so all objects have the intended flags.
  make -C "$WORK/lua-5.4.9" clean
  make -C "$WORK/lua-5.4.9" linux CC=clang \
    MYCFLAGS="$cflags" MYLDFLAGS="$ldflags"
  cp "$WORK/lua-5.4.9/src/lua" "$WORK/bin/lua-$config"
  "$WORK/bin/lua-$config" -v
done
