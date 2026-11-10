/* Database-local lookaside slots; internal allocation API needs the amalgamation here. */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <limits.h>
#include <stdlib.h>
#include "alloc.h"

#if ST_ANNOT
#error "SQLite lookaside has no verified custom-boundary annotation arm; use ANNOT=0"
#endif
#include "sqlite3.c"

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
