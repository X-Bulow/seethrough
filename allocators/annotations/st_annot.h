/* st_annot.h -- annotation macros an allocator calls. Expand to nothing when
 * ST_ANNOT is 0, so the unannotated arm is byte-identical allocator code.
 *
 * ASan:     ASAN_POISON_MEMORY_REGION / ASAN_UNPOISON_MEMORY_REGION  (<sanitizer/asan_interface.h>)
 * Valgrind: VALGRIND_CREATE_MEMPOOL / MEMPOOL_ALLOC / MEMPOOL_FREE / MAKE_MEM_NOACCESS  (<valgrind/memcheck.h>)
 * HWASan:   __hwasan_tag_memory / __hwasan_tag_pointer  (<sanitizer/hwasan_interface.h>)
 *
 * The build defines ST_TOOL_ASAN, ST_TOOL_VALGRIND or ST_TOOL_HWASAN (tools/flags.mk)
 * so the right header is pulled in. ASan and Valgrind can both be on at once (Valgrind
 * on an ASan binary is not a configuration we run, but the macros do not conflict).
 */
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

/* HWASan describes which allocation a pointer belongs to, not whether a byte is addressable.
 * The allocator gives each new object a fresh tag on its granules and returns a pointer that
 * carries it; when the object ends, its granules go back to the pool's own tag (the one
 * HWASan's malloc gave the backing block). A stale pointer keeps the old tag, so it mismatches
 * even after the storage is reissued. The allocator keeps its own pointers under the pool's
 * tag; ST_POOL_PTR turns a pointer the caller hands back into that form. Tags cover whole
 * 16-byte granules: the public interface cannot describe a short last granule, so slack up
 * to the next 16 bytes stays addressable (malloc's own short-granule encoding is internal). */
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
