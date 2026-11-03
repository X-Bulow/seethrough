# seethrough -- build one image of the matrix.
#
#   make image TOOL=asan ALLOC=arena ANNOT=1 CASE=heap-overflow-write CONTROL=0 OUT=build/x
#   make case  TOOL=asan ALLOC=malloc CASE=heap-overflow-write        # build + run the bug image
#   make control ...                                                   # build + run the control image
#   make control-image TOOL=asan SRC=corpus/controls/positive-uaf.c OUT=build/pc
#
# TOOL   asan | hwasan | ubsan | valgrind | lowfat | none      (tools/flags.mk)
# ALLOC  malloc | arena | freelist | memsys5 | lookaside | arena-rewrite | freelist-rewrite
# ANNOT  0 | 1
include tools/flags.mk

TOOL    ?= none
ALLOC   ?= malloc
ANNOT   ?= 0
CASE    ?= heap-overflow-write
CONTROL ?= 0
BUILD   ?= build
OUT     ?= $(BUILD)/$(CASE)-$(TOOL)-$(ALLOC)-a$(ANNOT)-$(if $(filter 1,$(CONTROL)),control,bug)

CASE_DIR := corpus/cases/$(CASE)
CASE_N   := $(shell python3 -c "import json;print(json.load(open('$(CASE_DIR)/case.json'))['case'])")

CC      := $(CC_$(TOOL))
OPT     ?= -O0 -g
INCS    := -Icorpus/include -Iallocators/annotations
DEFS    := -DST_ALLOC=$(ALLOC) -DST_ANNOT=$(ANNOT) -DST_CASE_N=$(CASE_N) $(if $(filter 1,$(CONTROL)),-DST_NEGATIVE_CONTROL,)
CFLAGS  := $(OPT) -Wall -Wextra -Wno-unused-parameter $(INCS) $(DEFS) $(CFLAGS_$(TOOL))
LDFLAGS := $(LD_$(TOOL))

# "arena-rewrite" lives in allocators/arena/rewrite/arena-rewrite.c
ALLOC_SRC := $(if $(findstring -rewrite,$(ALLOC)),allocators/$(subst -rewrite,,$(ALLOC))/rewrite/$(ALLOC).c,allocators/$(ALLOC)/$(ALLOC).c)
SRCS := harness/main.c $(CASE_DIR)/case.c $(ALLOC_SRC)

.PHONY: help image case control control-image clean
help:
	@sed -n '2,13p' Makefile

image: $(OUT)
$(OUT): $(SRCS) corpus/include/alloc.h corpus/include/harness.h tools/flags.mk
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(SRCS) -o $@ $(LDFLAGS)

case: image
	$(if $(filter valgrind,$(TOOL)),valgrind --error-exitcode=99 --leak-check=no,) ./$(OUT)

control:
	$(MAKE) case CONTROL=1 TOOL=$(TOOL) ALLOC=$(ALLOC) ANNOT=$(ANNOT) CASE=$(CASE)

# positive controls: plain C files with their own main(), no allocator layer
control-image:
	@mkdir -p $(dir $(OUT))
	$(CC) $(OPT) $(CFLAGS_$(TOOL)) $(SRC) -o $(OUT) $(LDFLAGS)

clean:
	rm -rf $(BUILD)
