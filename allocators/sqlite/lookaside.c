/* Database-local lookaside slots. The pinned amalgamation is linked separately. */
#include <limits.h>
#include <stdlib.h>
#include "alloc.h"
#include "sqlite3.h"

#if ST_ANNOT
#error "SQLite lookaside has no verified custom-boundary annotation arm; use ANNOT=0"
#endif

/* These three internal entry points are exported only in this test build. */
extern void *sqlite3DbMallocRaw(sqlite3 *, sqlite3_uint64);
extern void sqlite3DbFree(sqlite3 *, void *);
extern void *sqlite3DbRealloc(sqlite3 *, void *, sqlite3_uint64);

#define ST_LOOKASIDE_SLOT 128
#define ST_LOOKASIDE_COUNT 8192
static sqlite3 *db;
static void *buffer;
static size_t buffer_bytes;

void st_alloc_init(size_t bytes) {
    if (db || buffer) st_alloc_fini();
    size_t count = bytes ? bytes / ST_LOOKASIDE_SLOT : ST_LOOKASIDE_COUNT;
    if (count == 0 || count > INT_MAX) return;
    buffer_bytes = count * ST_LOOKASIDE_SLOT;
    buffer = malloc(buffer_bytes);
    if (!buffer) { buffer_bytes = 0; return; }
    if (sqlite3_open(":memory:", &db) != SQLITE_OK ||
        sqlite3_db_config(db, SQLITE_DBCONFIG_LOOKASIDE, buffer,
                          ST_LOOKASIDE_SLOT, (int)count) != SQLITE_OK) {
        st_alloc_fini();
    }
}
void *st_alloc(size_t n) {
    if (!db || !n) return NULL;
    return sqlite3DbMallocRaw(db, n);
}
void st_free(void *p) { if (db) sqlite3DbFree(db, p); }
void *st_realloc(void *p, size_t n) {
    if (!db) return NULL;
    if (!n) { sqlite3DbFree(db, p); return NULL; }
    return sqlite3DbRealloc(db, p, n);
}
void st_alloc_fini(void) {
    if (db) sqlite3_close(db);
    db = NULL;
    free(buffer);
    buffer = NULL;
    buffer_bytes = 0;
    sqlite3_shutdown();
}
const char *st_alloc_name(void) { return "lookaside"; }
size_t st_alloc_pool_bytes(void) { return buffer_bytes; }
