#include "harness.h"

/* Case 14 -- invalid free: a pointer into the middle of an object.
 *
 * One object, one free in both images; the defect passes a + 8 instead of a.
 * Real programs reach this by freeing a struct member, a pointer the program
 * advanced while parsing, or the payload of an object whose header the
 * allocator owns.
 *
 * glibc and ASan both reject it outright -- the chunk header is not where they
 * expect -- so this is the rare class where the malloc baseline is DETECTED by
 * the allocator itself and not only by the tool. Our arena looks a + 8 up in
 * its side table (B1.2), finds no object and leaves it alone; annotated, it
 * still hands a + 8 to VALGRIND_MEMPOOL_FREE. A free list pushes a + 8
 * onto a size-class list and later hands it out, so every subsequent object in
 * that class is misaligned with respect to the block it occupies: the damage is
 * real but shows up far from here, which is why the case records what it did
 * rather than relying on a crash.
 *
 * NEGATIVE CONTROL: frees a, the pointer st_alloc returned. */
ST_CASE(14) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_free(a);                /* the pointer st_alloc returned */
#else
    st_free(a + 8);            /* the defect: an interior pointer */
#endif
}
