#include "harness.h"

/* Case 10 -- use after free, write, after the storage was handed to someone else.
 *
 * The ceiling on what annotation can do, and the reason the free-list layer is
 * in the study. Free a, allocate b of the same size, and a free-list allocator
 * returns a's storage: now a and b are the same address, b is LIVE, and the
 * write through the stale a silently corrupts b's data.
 *
 * No poison-on-free annotation can catch this. At the moment of the access the
 * memory is legitimately live and must be unpoisoned, or b's own accesses would
 * be false positives. Only a tool that distinguishes the two POINTERS rather
 * than the memory -- a tag or a capability per allocation, so the stale pointer
 * carries the old identity -- can see it. That makes this the one row where
 * ASan with annotations stays MISSED while HWASan reports, but only where the
 * allocator gives b a new tag: HWASan's own malloc does, and so does the free
 * list's annotated arm; unannotated, a and b share the pool's tag.
 *
 * The case states its own precondition: "ST NOTE reuse=1" means the allocator
 * really did hand a's storage back. An arena that never reuses prints reuse=0,
 * and case.json's `requires` turns that row into UNSUPPORTED rather than
 * letting a vacuous pass read as a miss.
 *
 * NEGATIVE CONTROL: the write goes through b, the live pointer to that storage. */
ST_CASE(10) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    st_free(a);
    unsigned char *b = st_alloc(24);
    memset(b, 0x11, 24);
    printf("ST NOTE reuse=%d\n", (int)st_same_address(b, a));
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    b[0] = 0x22;               /* through the live pointer */
#else
    a[0] = 0x22;               /* the defect: through the stale one, into b's data */
#endif
    st_sink(b[0]);
    st_free(b);
}
