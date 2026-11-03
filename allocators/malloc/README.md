# malloc (baseline)

- Between two consecutive objects: the libc chunk header (glibc: 8 bytes usable-size word) and
  alignment padding to 16; under ASan, a redzone of at least 16 bytes.
- Reuse after free: glibc tcache returns the same chunk for the same size class immediately;
  under ASan, freed chunks go to a quarantine (256 MB by default) and are not reused soon.
- Size classes: glibc 16-byte steps up to tcache limits; usable size >= requested.
