# sqlite-speedtest1

Engine: `tools/fetch-sqlite.sh 3.53.3`. `speedtest1.c` is not in the amalgamation zip; it comes from the full 3.53.3 source tarball (`sqlite-src-3530300.zip`, same version or the benchmark and the engine disagree), fetched the same way once C5.1 starts.

TODO(C5.1): build.sh for each config (memsys5 / lookaside / rewrite x tool), run.sh writing the CSV.
