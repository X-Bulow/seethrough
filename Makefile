# seethrough -- build one image of the matrix.
#
#   make image TOOL=asan ALLOC=arena ANNOT=1 CASE=case00-heap-overflow-write CONTROL=0 OUT=build/x
#   make case  TOOL=asan ALLOC=malloc CASE=case00-heap-overflow-write        # build + run the bug image
#   make control ...                                                   # build + run the control image
#   make control-image TOOL=asan SRC=corpus/controls/positive-uaf.c OUT=build/pc
#   make real  TOOL=asan ARM=rewrite REAL=03-blob-close-after-db-close   # build + run a real SQLite case
#   make real-image TOOL=asan ARM=memsys5 REAL=... OUT=build/x
#
# TOOL   asan | hwasan | ubsan | valgrind | lowfat | none      (tools/flags.mk)
# ALLOC  malloc | arena | freelist | memsys5 | lookaside | arena-rewrite | freelist-rewrite
# ANNOT  0 | 1
# ARM    memsys5 | default | rewrite    (corpus/real only; see corpus/real/shared/repro322_common.h)
include tools/flags.mk

TOOL    ?= none
ALLOC   ?= malloc
ANNOT   ?= 0
CASE    ?= case00-heap-overflow-write
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

# ---------------------------------------------------------------- corpus/real (A7)
# Real SQLite 3.22.0 defects from capstone's engine-repros. The engine is compiled once per
# (tool, arm, engine group) into $(BUILD)/engine/ and linked with the case. SQLITE322 is the
# amalgamation directory from tools/fetch-sqlite.sh (lazy: only evaluated by these targets).
ARM      ?= rewrite
REAL     ?= 03-blob-close-after-db-close
REAL_DIR := corpus/real/$(REAL)
REAL_OUT ?= $(BUILD)/real-$(REAL)-$(TOOL)-$(ARM)
SQLITE322 = $(shell tools/fetch-sqlite.sh 3.22.0)
real_meta = $(shell python3 -c "import json;d=json.load(open('$(REAL_DIR)/case.json'));print($(1))")
REAL_GROUP = $(call real_meta,d['engine']['group'])
REAL_EFLAGS = $(call real_meta,' '.join(d['engine']['flags']))
REAL_SRCS = $(call real_meta,' '.join(d['sources']))
REAL_TAG = $(call real_meta,d['tag'])

# SQLITE_OMIT_COMPILEOPTION_DIAGS: the compile-option table cannot stringify "0,0".
ARMFLAGS_memsys5 := -DSQLITE_ENABLE_MEMSYS5 -DSQLITE_DEFAULT_LOOKASIDE=0,0 -DSQLITE_OMIT_COMPILEOPTION_DIAGS
ARMFLAGS_default :=
ARMFLAGS_rewrite := -DSQLITE_DEFAULT_LOOKASIDE=0,0 -DSQLITE_DEFAULT_PCACHE_INITSZ=0 -DSQLITE_OMIT_COMPILEOPTION_DIAGS
ENGINE_DEFS = -DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION $(ARMFLAGS_$(ARM)) $(REAL_EFLAGS)
ENGINE_OBJ = $(BUILD)/engine/sqlite3-$(TOOL)-$(ARM)-$(REAL_GROUP).o

.PHONY: real real-image engine
engine: $(ENGINE_OBJ)
$(ENGINE_OBJ): tools/flags.mk Makefile
	@mkdir -p $(dir $@)
	$(CC) $(OPT) -w $(CFLAGS_$(TOOL)) $(ENGINE_DEFS) -I$(SQLITE322) -c $(SQLITE322)/sqlite3.c -o $@

real-image: $(ENGINE_OBJ)
	@mkdir -p $(dir $(REAL_OUT))
	$(CC) $(OPT) -w $(CFLAGS_$(TOOL)) -DST_SQLITE_ARM=$(ARM) $(ENGINE_DEFS) -Icorpus/real/shared -I$(SQLITE322) \
	    $(REAL_DIR)/case.c $(REAL_SRCS) $(ENGINE_OBJ) -lm -o $(REAL_OUT) $(LD_$(TOOL))

real: real-image
	$(if $(filter valgrind,$(TOOL)),valgrind --error-exitcode=99 --leak-check=no,) ./$(REAL_OUT) $(REAL_TAG)

clean:
	rm -rf $(BUILD)
