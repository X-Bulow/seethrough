/* Positive control: a plain malloc 1-byte heap overflow write.
 * Every tool in the matrix must DETECT this before any case verdict counts. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char *p = malloc(64);
    memset(p, 0x5a, 64);
    puts("ST READY"); fflush(stdout);
    p[64] = 1;                           /* the defect */
    puts("ST DONE");
    free(p);
    return 0;
}
