/* st_annot.h -- annotation macros an allocator calls. Expand to nothing when
 * ST_ANNOT is 0, so the unannotated arm is byte-identical allocator code.
 *
 * ASan:     ASAN_POISON_MEMORY_REGION / ASAN_UNPOISON_MEMORY_REGION  (<sanitizer/asan_interface.h>)
 * Valgrind: VALGRIND_CREATE_MEMPOOL / MEMPOOL_ALLOC / MEMPOOL_FREE / MAKE_MEM_NOACCESS  (<valgrind/memcheck.h>)
 * HWASan:   no public CMA interface; the macros expand to nothing and the README says so.
 *
 * The build defines ST_TOOL_ASAN or ST_TOOL_VALGRIND (tools/flags.mk) so the
 * right header is pulled in. Both can be on at once (Valgrind on an ASan
 * binary is not a configuration we run, but the macros do not conflict).
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
#else
#  define ST_POOL_CREATE(pool, rz, zeroed)  ((void)0)
#  define ST_POOL_DESTROY(pool)             ((void)0)
#  define ST_POOL_ALLOC(pool, p, n)         ((void)0)
#  define ST_POOL_FREE(pool, p)             ((void)0)
#  define ST_NOACCESS(p, n)                 ((void)0)
#endif

#endif
