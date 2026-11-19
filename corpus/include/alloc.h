/* Shared allocator interface; select implementation with ST_ALLOC, annotations with ST_ANNOT.
 * st_alloc_init(bytes): initialize storage; 0 selects the default size.
 * st_alloc(n): return at least n usable bytes, aligned to 16 bytes (n > 0).
 * st_free(p): release an allocation; NULL is accepted.
 * st_realloc(p,n): may move; preserve min(old,n) bytes.
 * st_alloc_fini(): release backing storage; must be idempotent for case 12.
 * st_alloc_name(): allocator label for output.
 * st_alloc_pool_bytes(): backing pool size, or 0 without a pool; used by case 4.
 */
#ifndef SEETHROUGH_ALLOC_H
#define SEETHROUGH_ALLOC_H

#include <stddef.h>

#ifndef ST_ANNOT
#define ST_ANNOT 0
#endif

void        st_alloc_init(size_t bytes);
void       *st_alloc(size_t n);
void        st_free(void *p);
void       *st_realloc(void *p, size_t n);
void        st_alloc_fini(void);
const char *st_alloc_name(void);
size_t      st_alloc_pool_bytes(void);

#endif
