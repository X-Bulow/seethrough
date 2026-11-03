/* harness/main.c -- the one main() every case image links.
 * Built with -DST_CASE_N=<n>; prints the BEGIN marker, runs the case, prints DONE. */
#include <stdio.h>
#include <stdlib.h>
#include "harness.h"

#ifndef ST_CASE_N
#error "build with -DST_CASE_N=<case number>"
#endif
#define ST_CAT_(a, b) a##b
#define ST_CAT(a, b) ST_CAT_(a, b)
#define ST_CASE_FN ST_CAT(st_case_, ST_CASE_N)

void ST_CASE_FN(void);
volatile uintptr_t st_sink_slot;

int main(void) {
#ifdef ST_NEGATIVE_CONTROL
    const int control = 1;
#else
    const int control = 0;
#endif
    st_alloc_init(0);
    printf("ST BEGIN case=%d alloc=%s annot=%d control=%d\n", ST_CASE_N, st_alloc_name(), ST_ANNOT, control);
    fflush(stdout);
    ST_CASE_FN();
    st_alloc_fini();
    puts("ST DONE");
    return 0;
}
