#!/usr/bin/env bash
# Week-1 HWASan feasibility probe (TASKS C3.2). Run on the server; paste the output into docs/hwasan.md.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/corpus/controls/positive-uaf.c"
OUT="${TMPDIR:-/tmp}/st-hwasan-probe"
echo "== cpu lam flag: $(grep -c -w lam /proc/cpuinfo 2>/dev/null)   kernel: $(uname -r)   clang: $(clang --version | head -1)"
echo "== native x86-64"
if clang -fsanitize=hwaddress -O0 -g "$SRC" -o "$OUT" 2>&1; then
  "$OUT"; echo "exit=$?"
else
  echo "native build failed"
fi
echo "== fallback A: aarch64 cross + qemu-user (needs clang target support, an aarch64 sysroot, qemu-aarch64)"
if command -v qemu-aarch64 >/dev/null; then
  # lld: GNU ld turns the MOVK that tags a global's address into an undefined instruction (SIGILL)
  clang --target=aarch64-linux-gnu -fuse-ld=lld -fsanitize=hwaddress -O0 -g "$SRC" -o "$OUT-a64" 2>&1 && qemu-aarch64 "$OUT-a64"; echo "exit=$?"
else
  echo "qemu-aarch64 not installed"
fi
