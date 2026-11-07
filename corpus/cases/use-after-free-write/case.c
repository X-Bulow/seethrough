#include "harness.h"

/* Case 8 -- use after free, write, with no allocation in between.
 *
 * The simplest temporal defect: one object, freed, then written through the
 * stale pointer. Nothing has reused the storage yet, so what the tools have to
 * work with is only the fact that the lifetime ended.
 *
 * That is exactly what a custom allocator does not record. malloc puts the
 * block in a quarantine and ASan paints its shadow "freed"; a bump-pointer
 * arena's st_free is a no-op, so the bytes are as live after the free as
 * before, and there is nothing for any malloc-granular tool to see. An
 * annotated arena has to poison the object at free time to win this back,
 * which needs the object's size -- and a bump arena does not keep it (see the
 * TODO in allocators/arena/arena.c).
 *
 * NEGATIVE CONTROL: the same single alloc and single free, with the write
 * before the free instead of after it. */
ST_CASE(8) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
#ifdef ST_NEGATIVE_CONTROL
    ST_READY();
    a[0] = 1;                  /* while still live */
    st_free(a);
#else
    st_free(a);
    ST_READY();
    a[0] = 1;                  /* the defect: after the free */
#endif
}
