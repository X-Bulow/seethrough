/* Baseline: every request goes straight to libc. */
#include <stdlib.h>
#include "alloc.h"

void        st_alloc_init(size_t bytes) { (void)bytes; }
void       *st_alloc(size_t n)          { return malloc(n); }
void        st_free(void *p)            { free(p); }
void       *st_realloc(void *p, size_t n) { return realloc(p, n); }
void        st_alloc_fini(void)         { }
const char *st_alloc_name(void)         { return "malloc"; }
