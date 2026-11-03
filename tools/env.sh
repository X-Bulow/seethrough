#!/usr/bin/env bash
# Print the environment record that goes into every results bundle as env.txt.
echo "date: $(date -u +%FT%TZ)"
echo "host: $(hostname)  uname: $(uname -srm)"
if [ -r /proc/cpuinfo ]; then
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')  cores: $(nproc)"
  echo "lam: $(grep -c -w lam /proc/cpuinfo) (nonzero = CPU reports Linear Address Masking; needed for native x86-64 HWASan)"
fi
echo "git: $(git -C "$(dirname "$0")/.." rev-parse --short HEAD 2>/dev/null) dirty=$(git -C "$(dirname "$0")/.." status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
for t in clang gcc valgrind qemu-aarch64; do
  printf '%s: ' "$t"; command -v "$t" >/dev/null && "$t" --version 2>/dev/null | head -1 || echo missing
done
echo "ldd: $(ldd --version 2>/dev/null | head -1)"
