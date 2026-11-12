/* harness.h -- what a case.c includes.
 *
 *   ST_CASE(n)            defines the case body; harness/main.c calls it
 *   ST_READY()            print the "ST READY" line right before the invalid access
 *   ST_NEGATIVE_CONTROL   defined by the build for the control image
 *   st_sink(x)            forces a read to be observed (defeats dead-load elimination)
 *   st_same_address(a, b) whether two pointers name the same address, ignoring a tag
 *
 * Markers the classifier looks for on stdout:
 *   "ST BEGIN case=<n> alloc=<name> annot=<0|1> control=<0|1>"
 *   "ST READY"            the defect is about to execute
 *   "ST DONE"             the case returned; with no tool report this is MISSED
 */
#ifndef SEETHROUGH_HARNESS_H
#define SEETHROUGH_HARNESS_H

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "alloc.h"

#define ST_CASE(n) void st_case_##n(void)

#define ST_READY() do { puts("ST READY"); fflush(stdout); } while (0)

/* A global the optimiser cannot prove unused; cases write loaded values here. */
extern volatile uintptr_t st_sink_slot;
#define st_sink(x) do { st_sink_slot = (uintptr_t)(x); } while (0)

/* HWASan keeps a tag in a pointer's top byte, so a reissued block compares unequal under ==
 * even at the same address. The precondition markers ask about the address. x86-64 user
 * addresses never set the top byte, so the mask changes nothing for the other tools. */
#define st_same_address(a, b) \
    (((uintptr_t)(a) & (((uintptr_t)1 << 56) - 1)) == ((uintptr_t)(b) & (((uintptr_t)1 << 56) - 1)))

/* The pattern a case fills live objects with, so a stale read has something to see. */
#define ST_FILL 0x5a

#endif
