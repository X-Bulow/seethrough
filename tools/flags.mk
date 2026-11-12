# Per-tool flags. Included by the top-level Makefile. TODO(C1.3): verify on the server.
# Detection builds are -O0 -g so the compiler cannot delete the defect; Q2 benchmarks are -O2.
CC_asan      := clang
CFLAGS_asan  := -fsanitize=address -fno-omit-frame-pointer -DST_TOOL_ASAN
LD_asan      := -fsanitize=address

# HWASan runs only on aarch64 Linux here (docs/hwasan.md). lld, because GNU ld 2.46 rewrites
# the MOVK that puts a global's tag in its address into an undefined instruction (SIGILL).
CC_hwasan     := clang
CFLAGS_hwasan := -fsanitize=hwaddress -fno-omit-frame-pointer -DST_TOOL_HWASAN
LD_hwasan     := -fsanitize=hwaddress -fuse-ld=lld

CC_ubsan      := clang
CFLAGS_ubsan  := -fsanitize=bounds,object-size -fno-sanitize-recover=all -DST_TOOL_UBSAN
LD_ubsan      := -fsanitize=bounds,object-size

CC_valgrind     := gcc
CFLAGS_valgrind := -DST_TOOL_VALGRIND
LD_valgrind     :=

CC_lowfat      := $(SEETHROUGH_TOOLS)/lowfat/bin/clang   # TODO(C4.1)
CFLAGS_lowfat  := -fsanitize=lowfat -DST_TOOL_LOWFAT
LD_lowfat      := -fsanitize=lowfat

CC_none      := cc
CFLAGS_none  :=
LD_none      :=
