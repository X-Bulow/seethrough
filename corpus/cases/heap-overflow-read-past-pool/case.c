#include "harness.h"

/* Case 4 -- heap overflow, read, past the end of the allocator's own block.
 *
 * The control case for every other overflow row, and the reason the real
 * SQLite fuzz cases in corpus/real behave as they do. An access that stays
 * inside the pool is invisible to a malloc-granular tool; an access that LEAVES
 * the pool is a plain overflow of the one block the allocator itself took from
 * malloc, so every tool recovers its sight. Detection here is not evidence that
 * the tool understands the custom allocator -- it is evidence that it does not
 * have to.
 *
 * The offset is computed, never assumed: every st_alloc result is at or after
 * the pool's base, so a + pool_bytes + 64 is past the pool's end wherever a
 * landed. With no pool (malloc) the container is the object itself, so the case
 * degenerates to case 1 and reads one byte past the end -- which must be
 * DETECTED, and that is what makes the malloc column the baseline for the row.
 *
 * NEGATIVE CONTROL: reads a[23]. */
ST_CASE(4) {
    size_t pool = st_alloc_pool_bytes();
    size_t off = pool ? pool + 64 : 24;
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    printf("ST NOTE pool_bytes=%zu offset=%zu\n", pool, off);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_sink(a[23]);            /* last valid byte */
#else
    st_sink(a[off]);           /* the defect: outside the container, not just the object */
#endif
    st_free(a);
}
