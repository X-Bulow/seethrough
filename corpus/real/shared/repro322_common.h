/* repro322_common.h -- seethrough's implementation of the interface the capstone
 * engine-repros cases are written against, so every case.c in corpus/real/ is the
 * upstream file byte for byte (PROVENANCE.md records the sha256).
 *
 * The capstone original (capstone/ports/sqlite/repro322/repro322_common.h) gives a case
 * five things: out_text, out_uint, repro_init, FAILRC and REPRO322_MAIN. This file gives
 * the same five over libc and selects the allocator arm with -DST_SQLITE_ARM:
 *
 *   memsys5   sqlite3_config(SQLITE_CONFIG_HEAP) over one 256 KiB static array, lookaside
 *             off: every SQLite object is carved out of sqlite_heap[] by memsys5, and the
 *             tool below sees one object and no frees. Capstone's measured arm.
 *   default   SQLite as shipped: no memsys5; lookaside on (small connection-owned objects
 *             come from a per-connection slab) and the page-cache bulk pool on (page buffers
 *             come from one block). Which layer holds the stale or overrun object is a
 *             per-case fact, recorded in case.json.
 *   rewrite   no memsys5, lookaside 0,0, pcache bulk 0: every object is its own malloc
 *             block. The professor's "undo the CMA" and the positive control for the
 *             other two arms: an ASan run on this arm must report the bug or the case
 *             gives no verdict at all.
 *
 * Markers for harness/classify.py: REPRO322_MAIN prints "ST BEGIN" before the body and
 * "ST DONE" after it; repro_init prints "ST READY" once the engine is configured. READY
 * here means "the body started", not "the invalid access is next" as it does in
 * corpus/cases/: the access is inside SQLite. Each case prints its own reachability line
 * (case.json "reached"), and harness/run-real.py requires that line before it reads a
 * silent run as MISSED. */
#ifndef REPRO322_COMMON_H
#define REPRO322_COMMON_H

#include "sqlite3.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ST_ARM_memsys5 1
#define ST_ARM_default 2
#define ST_ARM_rewrite 3
#define ST_ARM_CAT_(a) ST_ARM_##a
#define ST_ARM_CAT(a) ST_ARM_CAT_(a)
#ifndef ST_SQLITE_ARM
#error "build with -DST_SQLITE_ARM=memsys5|default|rewrite"
#endif
#define ST_ARM ST_ARM_CAT(ST_SQLITE_ARM)
#define ST_STR_(a) #a
#define ST_STR(a) ST_STR_(a)

static void out_text(const char *text) { fputs(text, stdout); }
static void out_uint(unsigned long v) { printf("%lu", v); }
static int run_case(void);

#ifndef SQLITE_HEAP_SIZE
#define SQLITE_HEAP_SIZE (256U * 1024U)   /* capstone: the same on every arm, corpus322.sh passes 262144 */
#endif
#ifndef SQLITE_HEAP_MIN_REQ
#define SQLITE_HEAP_MIN_REQ 64
#endif
#if ST_ARM == ST_ARM_memsys5
static unsigned char sqlite_heap[SQLITE_HEAP_SIZE] __attribute__((aligned(16)));
#endif

static int repro_init(void) {
  int rc;
#if ST_ARM == ST_ARM_memsys5
  rc = sqlite3_config(SQLITE_CONFIG_HEAP, sqlite_heap, (int)sizeof sqlite_heap, SQLITE_HEAP_MIN_REQ);
  if (rc != SQLITE_OK) {
    /* Never fall through to malloc: that would silently turn this arm into the rewrite arm. */
    out_text("CONTROL-FAILED config-heap rc="); out_uint((unsigned)rc);
    out_text(" (build the amalgamation with SQLITE_ENABLE_MEMSYS5)\n");
    return rc;
  }
  out_text("repro allocator=memsys5 heap_bytes="); out_uint(sizeof sqlite_heap); out_text("\n");
#elif ST_ARM == ST_ARM_default
  out_text("repro allocator=malloc lookaside=default pcache_bulk=default\n");
#else
  out_text("repro allocator=malloc lookaside=off pcache_bulk=off\n");
#endif
  rc = sqlite3_initialize();
  if (rc != SQLITE_OK) {
    out_text("CONTROL-FAILED initialize rc="); out_uint((unsigned)rc); out_text("\n");
    return rc;
  }
  puts("ST READY"); fflush(stdout);
  return 0;
}

/* The tag on the command line is capstone's fixture check: an image told to run another
 * case refuses (exit 75) instead of reporting under the wrong name. */
#define REPRO322_MAIN(TAG)                                                        \
  int main(int argc, char **argv) {                                               \
    setvbuf(stdout, NULL, _IONBF, 0);                                             \
    if (argc > 1 && strcmp(argv[1], (TAG))) {                                     \
      fprintf(stderr, "CONTROL-FAILED fixture is %s, run asked for %s\n", (TAG), argv[1]); \
      return 75;                                                                  \
    }                                                                             \
    printf("ST BEGIN case=%s arm=%s sqlite=%s\n", (TAG), ST_STR(ST_SQLITE_ARM), sqlite3_libversion()); \
    (void)run_case();                                                             \
    sqlite3_shutdown();                                                           \
    puts("ST DONE");                                                              \
    return 0;                                                                     \
  }

#define FAILRC(stage, rc) (out_text(stage), out_text(" rc="), \
  out_uint((unsigned long)((rc) < 0 ? -(rc) : (rc))), out_text("\n"), (rc) ? (rc) : 1)

#endif
