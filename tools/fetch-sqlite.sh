#!/usr/bin/env bash
# Fetch one pinned SQLite amalgamation and print the directory holding sqlite3.c / sqlite3.h.
#
#   tools/fetch-sqlite.sh 3.22.0     # corpus/real: the engine bugs are live in this release
#   tools/fetch-sqlite.sh 3.53.3     # allocators/sqlite (memsys5, lookaside) and benchmarks/sqlite-speedtest1
#
# The source is never committed (sqlite3.c alone is 8-9 MB). It lives in $SEETHROUGH_CACHE,
# default <repo>/vendor/ (gitignored). Not /tmp: on the lab server /tmp is shared and cleared on
# reboot, and a pin that has to be re-fetched is one reboot away from "which bytes did we run".
#
# Both pins are the ones project-starch/llvm-capstone (dev) uses, so our cells are comparable
# with its bug-corpora: 3.22.0 is the release of capstone/bug-corpora/sqlite/engine-repros
# (stock amalgamation sha256 7991acd0..., recorded in its corpus bundles), 3.53.3 is its general
# port (capstone/ports/sqlite/fetch-sqlite.sh, SHA3-256 d45c688a... of the zip). The hashes below
# were computed from sqlite.org downloads on 2026-11-05 and agree with capstone's.
#
# Only the zip hash gates the fetch. The sqlite3.c hash is checked too so that a cache that
# someone edited in place (an annotation patch applied by hand, say) is refused rather than
# silently built. Patches go through allocators/sqlite/*.patch at build time, never into vendor/.
set -euo pipefail

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
CACHE=${SEETHROUGH_CACHE:-$REPO/vendor}

case "${1:-}" in
  3.22.0)
    YEAR=2018; NUM=3220000
    ZIP_SHA256=0db7cb47613475c5060ce47ad24dc73875cddeda4d13196ab3a98b356326ac72
    C_SHA256=7991acd0d8c78435d47523a43aeeb117f0aa264c4d7d0d10410f0128ed1f6004
    ;;
  3.53.3)
    YEAR=2026; NUM=3530300
    ZIP_SHA256=646421e12aac110282ef8cc68f1a62d4bb15fc7b8f09da0b53e29ee690500431
    C_SHA256=87497ab605bedd0dbee27a209c1eeff8c89b229b13f921a7efdbb81a13f779fd
    ;;
  *)
    echo "usage: $0 3.22.0|3.53.3   (prints the amalgamation directory)" >&2
    exit 2
    ;;
esac

NAME=sqlite-amalgamation-$NUM
URL=https://www.sqlite.org/$YEAR/$NAME.zip
ZIP=$CACHE/$NAME.zip
DIR=$CACHE/$NAME

sha256() { python3 -I -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }

mkdir -p "$CACHE"
if [ ! -f "$ZIP" ]; then
  echo "fetch-sqlite: downloading $URL" >&2
  curl -fsSL "$URL" -o "$ZIP.part" && mv "$ZIP.part" "$ZIP"
fi
got=$(sha256 "$ZIP")
if [ "$got" != "$ZIP_SHA256" ]; then
  echo "fetch-sqlite: $ZIP sha256 $got, pinned $ZIP_SHA256; refusing (delete it to re-download)" >&2
  exit 1
fi
if [ ! -f "$DIR/sqlite3.c" ] || [ ! -f "$DIR/sqlite3.h" ]; then
  python3 -I -c 'import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' "$ZIP" "$CACHE"
fi
got=$(sha256 "$DIR/sqlite3.c")
if [ "$got" != "$C_SHA256" ]; then
  echo "fetch-sqlite: $DIR/sqlite3.c sha256 $got, pinned $C_SHA256; the cache was modified, refusing" >&2
  exit 1
fi
grep -q "define SQLITE_VERSION *\"$1\"" "$DIR/sqlite3.h"
echo "$DIR"
