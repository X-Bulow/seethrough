# Running with HWASan

The committed HWASan matrix uses an aarch64 Linux VM on Apple Silicon. The lab x86-64 machines lack LAM and cannot run the default HWASan runtime. Native macOS does not support this sanitizer configuration.

## Environment and execution

The recorded environment uses Lima with Apple Virtualization.framework, Ubuntu 26.04.1 aarch64, clang 21.1.8, and lld 21.1.8. Run from the repository root on the Mac host, then execute the VM commands as indicated:

```bash
brew install lima
limactl start --name=seethrough-hwasan --vm-type=vz --cpus=4 --memory=4 --disk=20 \
  --containerd=none --mount-only="$PWD" template:ubuntu-26.04     # Run at repository root; mount it read-only
limactl shell seethrough-hwasan
# Run the following inside the VM
sudo apt-get update
sudo apt-get install -y clang=1:21.1.6-71 clang-21=1:21.1.8-6ubuntu1 lld-21=1:21.1.8-6ubuntu1 make python3
git clone <mounted-repository-path> ~/seethrough && cd ~/seethrough      # Mount is read-only; write results in the clone
python3 harness/run-matrix.py --tools hwasan --allocs malloc arena freelist --annots 0 1 \
  --cases all --out results/<bundle>
```

Stop with `limactl stop seethrough-hwasan` and resume with `limactl start seethrough-hwasan`. Results are written in the VM's writable clone; the host repository mount is read-only.

Link with `-fuse-ld=lld`, as configured in `tools/flags.mk`. GNU ld 2.46 can mishandle tagged-global address relocations and turn a MOVK into an undefined instruction, causing SIGILL even in the positive control. Both malloc overflow and UAF positive controls must pass before the matrix is accepted.

## Annotation behavior

`st_annot.h` uses `__hwasan_tag_memory`, `__hwasan_tag_pointer`, and `__hwasan_get_tag_from_pointer` from `<sanitizer/hwasan_interface.h>`. Allocations receive a fresh tag; freeing restores the pool tag. Allocator bookkeeping accesses use the pool tag through `ST_POOL_PTR`.

The public tagging interface operates on 16-byte granules and cannot express the short final granules used by HWASan's own malloc. Small overflows into alignment slack can remain undetected after annotation. Detection is also probabilistic: tag collisions can permit invalid accesses, so a single run need not match a deterministic expectation.

## Platform limits

Clang's experimental x86-64 aliasing mode can run without LAM, but in the tested environment it leaves heap blocks above 64 KiB outside the checked alias region. The arena and freelist pools are 1 MiB, so their accesses remain unchecked even with annotations. Its 3-bit pointer tags also do not support the allocator's 16–255 tag range. This mode is excluded from the matrix.

HWASan results come from a different architecture and host than ASan and Valgrind results. They are used for detection comparisons only; the repository does not compare HWASan timing or RSS with the x86-64 benchmarks.
