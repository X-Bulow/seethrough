/* Shared ASan, Memcheck, and HWASan hooks; no-ops when ST_ANNOT=0.
 * ST_TOOL_* selects the detector interface (tools/flags.mk). */
#ifndef SEETHROUGH_ANNOT_H
#define SEETHROUGH_ANNOT_H

#include <stddef.h>

#if ST_ANNOT && defined(ST_TOOL_ASAN)
#  include <sanitizer/asan_interface.h>
#  define ST_POISON(p, n)     ASAN_POISON_MEMORY_REGION((p), (n))
#  define ST_UNPOISON(p, n)   ASAN_UNPOISON_MEMORY_REGION((p), (n))
#else
#  define ST_POISON(p, n)     ((void)0)
#  define ST_UNPOISON(p, n)   ((void)0)
#endif

#if ST_ANNOT && defined(ST_TOOL_VALGRIND)
#  include <valgrind/memcheck.h>
#  define ST_POOL_CREATE(pool, rz, zeroed)  VALGRIND_CREATE_MEMPOOL((pool), (rz), (zeroed))
#  define ST_POOL_DESTROY(pool)             VALGRIND_DESTROY_MEMPOOL((pool))
#  define ST_POOL_ALLOC(pool, p, n)         VALGRIND_MEMPOOL_ALLOC((pool), (p), (n))
#  define ST_POOL_FREE(pool, p)             VALGRIND_MEMPOOL_FREE((pool), (p))
#  define ST_NOACCESS(p, n)                 VALGRIND_MAKE_MEM_NOACCESS((p), (n))
#  define ST_DEFINED(p, n)                  VALGRIND_MAKE_MEM_DEFINED((p), (n))
#else
#  define ST_POOL_CREATE(pool, rz, zeroed)  ((void)0)
#  define ST_POOL_DESTROY(pool)             ((void)0)
#  define ST_POOL_ALLOC(pool, p, n)         ((void)0)
#  define ST_POOL_FREE(pool, p)             ((void)0)
#  define ST_NOACCESS(p, n)                 ((void)0)
#  define ST_DEFINED(p, n)                  ((void)0)
#endif

/* Fresh object tags distinguish stale pointers after reuse; free restores the pool tag.
 * ST_POOL_PTR retags allocator bookkeeping accesses. Public tags cover 16-byte granules,
 * so alignment slack cannot be checked at byte precision. */
#if ST_ANNOT && defined(ST_TOOL_HWASAN)
#  include <stdint.h>
#  include <sanitizer/hwasan_interface.h>
static inline void *st_hwasan_tag_new(const void *pool, void *p, size_t n) {
    /* 1..15 in a shadow byte mean "short granule", so object tags start at 16. Consecutive
     * tags keep bump neighbours apart and give a reissued slot a tag its last owner lacked. */
    static unsigned char next = 15;
    unsigned char pool_tag = __hwasan_get_tag_from_pointer(pool);
    do next = next == 255 ? 16 : next + 1; while (next == pool_tag);
    __hwasan_tag_memory(p, next, (n + 15) & ~(size_t)15);
    return __hwasan_tag_pointer(p, next);
}
static inline void st_hwasan_tag_pool(const void *pool, const void *p, size_t n) {
    uintptr_t lo = (uintptr_t)p & ~(uintptr_t)15;
    uintptr_t hi = ((uintptr_t)p + n + 15) & ~(uintptr_t)15;
    __hwasan_tag_memory((const void *)lo, __hwasan_get_tag_from_pointer(pool), hi - lo);
}
#  define ST_TAG_NEW(pool, p, n)   st_hwasan_tag_new((pool), (p), (n))
#  define ST_TAG_POOL(pool, p, n)  st_hwasan_tag_pool((pool), (p), (n))
#  define ST_POOL_PTR(pool, p)     __hwasan_tag_pointer((p), __hwasan_get_tag_from_pointer(pool))
#else
#  define ST_TAG_NEW(pool, p, n)   (p)
#  define ST_TAG_POOL(pool, p, n)  ((void)0)
#  define ST_POOL_PTR(pool, p)     (p)
#endif

#endif
