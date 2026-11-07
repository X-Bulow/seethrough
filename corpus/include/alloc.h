/* alloc.h -- the one allocator interface every case uses.
 *
 * A case never calls malloc. It calls st_alloc / st_free / st_realloc, and the
 * build picks the implementation with -DST_ALLOC=<name>, linking
 * allocators/<name>/<name>.c. Annotations (ASan poisoning, Valgrind mempool)
 * live inside the allocator and are switched on with -DST_ANNOT=1, so a case
 * is identical across all cells of the matrix.
 *
 * Contract (B implements, A relies on):
 *   st_alloc_init(bytes)   create the backing arena; bytes is a hint, 0 = default
 *   st_alloc(n)            n > 0; returns at least n usable bytes, 16-byte aligned
 *   st_free(p)             p from st_alloc, or NULL
 *   st_realloc(p, n)       may move; preserves min(old, n) bytes
 *   st_alloc_fini()        release the backing store (so Valgrind sees no leak noise);
 *                          must be IDEMPOTENT -- case 12 ends the pool's lifetime itself and
 *                          harness/main.c calls fini again afterwards
 *   st_alloc_name()        "malloc" | "arena" | "freelist" | "memsys5" | "lookaside"
 *   st_alloc_pool_bytes()  the size of the block this allocator carves from, 0 if it has none
 *                          (malloc). Only the corpus uses it, and only to locate the pool's
 *                          outer boundary: case 4 needs an offset that is certainly outside
 *                          the container, and no case may assume a number. Since every
 *                          st_alloc result is at or after the pool's base, p + pool_bytes is
 *                          past the pool's end wherever p landed.
 *
 * Layout promises each allocator must document in allocators/<name>/README.md:
 *   - what sits between two consecutive st_alloc(n) results (header? padding? nothing?)
 *   - whether st_free(p) followed by st_alloc(same n) can return p again, and how soon
 *   - the size classes, if any, and their slack
 * Those three facts are what the Q1 table is about.
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
