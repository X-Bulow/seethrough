/* Positive control: a plain malloc use-after-free read.
 * Every tool in the matrix must DETECT this before any case verdict counts.
 * Deliberately does NOT go through alloc.h: it tests the tool, not the allocator. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

volatile unsigned long sink;

int main(void) {
    char *p = malloc(64);
    memset(p, 0x5a, 64);
    free(p);
    puts("ST READY"); fflush(stdout);
    sink = (unsigned char)p[8];          /* the defect */
    puts("ST DONE");
    return 0;
}
