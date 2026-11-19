/* Fixed allocation/reuse workload for measuring annotation overhead. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "alloc.h"

int main(int argc, char **argv) {
    int cycles = argc > 1 ? atoi(argv[1]) : 10000;
    unsigned long checksum = 0;
    struct timespec started, stopped;
    if (cycles <= 0) return 2;
    if (clock_gettime(CLOCK_MONOTONIC, &started)) return 5;
    for (int c = 0; c < cycles; ++c) {
        unsigned char *p[128];
        st_alloc_init(0);
        for (int i = 0; i < 128; ++i) {
            size_t n = i & 1 ? 64 : 24;
            p[i] = st_alloc(n);
            if (!p[i]) return 3;
            memset(p[i], (unsigned char)i, n);
        }
        for (int i = 0; i < 128; i += 2) st_free(p[i]);
        for (int i = 0; i < 128; i += 2) {
            p[i] = st_alloc(24);
            if (!p[i]) return 4;
            p[i][0] = (unsigned char)(i + c);
        }
        for (int i = 0; i < 128; ++i) {
            checksum += p[i][0];
            st_free(p[i]);
        }
        st_alloc_fini();
    }
    if (clock_gettime(CLOCK_MONOTONIC, &stopped)) return 5;
    double elapsed = (stopped.tv_sec - started.tv_sec) +
                     (stopped.tv_nsec - started.tv_nsec) / 1e9;
    printf("cycles=%d checksum=%lu elapsed_seconds=%.6f\n", cycles, checksum, elapsed);
    return 0;
}
