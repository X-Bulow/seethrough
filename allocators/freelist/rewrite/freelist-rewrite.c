/* Rewrite the free-list interface to individual libc allocations. */
#include <stdlib.h>
#include "alloc.h"

void st_alloc_init(size_t bytes) { (void)bytes; }
void *st_alloc(size_t n) { return n ? malloc(n) : NULL; }
void st_free(void *p) { free(p); }
void *st_realloc(void *p, size_t n) {
    if (!n) { free(p); return NULL; }
    return realloc(p, n);
}
void st_alloc_fini(void) {}
const char *st_alloc_name(void) { return "freelist-rewrite"; }
size_t st_alloc_pool_bytes(void) { return 0; }
