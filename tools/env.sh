#!/usr/bin/env bash
# Print the environment record that goes into every results bundle as env.txt.
echo "date: $(date -u +%FT%TZ)"
echo "host: $(hostname)  uname: $(uname -srm)"
if [ -r /proc/cpuinfo ]; then
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')  cores: $(nproc)"
  echo "lam: $(grep -c -w lam /proc/cpuinfo) (nonzero = CPU reports Linear Address Masking; needed for native x86-64 HWASan)"
fi
# results/ is not counted: the bundle this record is written into, and the earlier bundles of the
# same run, stay untracked until they are committed. Anything else not committed is listed.
root="$(dirname "$0")/.."
dirty="$(git -C "$root" status --porcelain -- . ':(exclude)results' 2>/dev/null)"
echo "git: $(git -C "$root" rev-parse --short HEAD 2>/dev/null) dirty=$(printf '%s' "$dirty" | grep -c .) (results/ not counted)"
if [ -n "$dirty" ]; then printf '%s\n' "$dirty" | sed 's/^/  /'; fi
for t in clang gcc valgrind qemu-aarch64; do
  printf '%s: ' "$t"; command -v "$t" >/dev/null && "$t" --version 2>/dev/null | head -1 || echo missing
done
echo "ldd: $(ldd --version 2>/dev/null | head -1)"

echo "flags (tools/flags.mk):"
cat "$(dirname "$0")/flags.mk"
