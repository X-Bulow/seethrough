#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$ROOT/build/sqlite-speedtest1"
mkdir -p "$WORK/src" "$WORK/bin"

curl -fL https://www.sqlite.org/2025/sqlite-amalgamation-3500400.zip \
  -o "$WORK/amalgamation.zip"
curl -fL https://www.sqlite.org/2025/sqlite-src-3500400.zip \
  -o "$WORK/source.zip"

unzip -jo "$WORK/amalgamation.zip" \
  '*/sqlite3.c' '*/sqlite3.h' -d "$WORK/src"
unzip -jo "$WORK/source.zip" \
  '*/test/speedtest1.c' -d "$WORK/src"
sha256sum "$WORK/src/"*.c "$WORK/src/sqlite3.h" > "$WORK/SHA256SUMS"
