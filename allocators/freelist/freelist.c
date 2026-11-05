/* Free-list allocator: fixed size classes, LIFO free lists carved from arena blocks.
 * TODO(B1.3): implement. The point of this layer is immediate reuse: st_free(p)
 * then st_alloc(same class) must return p, so a use-after-free reads another
 * object's bytes (or the free-list link). */
#include <stdlib.h>
#include "alloc.h"
#include "st_annot.h"

void        st_alloc_init(size_t bytes) { (void)bytes; }
void       *st_alloc(size_t n)          { return malloc(n); /* TODO(B1.3) placeholder */ }
void        st_free(void *p)            { free(p);          /* TODO(B1.3) placeholder */ }
void       *st_realloc(void *p, size_t n) { return realloc(p, n); }
void        st_alloc_fini(void)         { }
const char *st_alloc_name(void)         { return "freelist"; }
size_t      st_alloc_pool_bytes(void)   { return 0; /* TODO(B1.3): the size of the block the size classes are carved from */ }
