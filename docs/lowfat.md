# LowFat build and validation

Environment: Ubuntu 18.04 Docker container inside the lab VirtualBox VM, glibc `2.27-3ubuntu1.6`; the resulting compiler is clang 4.0.0. Upstream: https://github.com/GJDuck/LowFat; commit: `20f8075dd1fd6588700262353c7ba619d82cea8f`.

Build from the project root (requires Docker; the directory and container names below must not already exist):

```bash
set -euo pipefail
mkdir -p build
git clone https://github.com/GJDuck/LowFat build/LowFat-ubuntu18
git -C build/LowFat-ubuntu18 checkout --detach \
  20f8075dd1fd6588700262353c7ba619d82cea8f
sudo docker run --name seethrough-lowfat18 --cpuset-cpus=0,1 \
  --mount "type=bind,src=$PWD/build/LowFat-ubuntu18,dst=/work" \
  --workdir /work ubuntu:18.04 bash -c '
    set -euo pipefail
    sed -i "s|http://archive.ubuntu.com/ubuntu|http://sg.archive.ubuntu.com/ubuntu|g" /etc/apt/sources.list
    apt-get update
    apt-get install -y --no-install-recommends \
      build-essential cmake python zlib1g-dev libtinfo-dev xz-utils
    bash build.sh 2>&1 | tee build.log
  '
sudo docker commit seethrough-lowfat18 seethrough-lowfat18:built
```

Compiler path inside the container: `/work/build/bin/clang`. Build log: `build/LowFat-ubuntu18/build.log`.

Create a boundary validation program on the Ubuntu host:

```bash
mkdir -p build/lowfat-controls
cat > build/lowfat-controls/bounds-check.c <<'EOF'
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    char *p = malloc(64);
    if (!p) return 2;
    volatile size_t index = argc > 1 ? 128 : 0;
    puts("ST READY");
    fflush(stdout);
    p[index] = 1;
    puts("ST DONE");
    free(p);
    return 0;
}
EOF
```

Compile and run the original controls and boundary validation program in the same container environment:

```bash
sudo docker run --rm --volumes-from seethrough-lowfat18 \
  --mount "type=bind,src=$PWD,dst=/project" --workdir /project \
  seethrough-lowfat18:built bash -c '
    set -eu
    for name in positive-overflow positive-uaf; do
      /work/build/bin/clang -O0 -g -fsanitize=lowfat \
        "corpus/controls/$name.c" -o "build/lowfat-controls/$name"
      status=0
      "build/lowfat-controls/$name" \
        > "build/lowfat-controls/$name.log" 2>&1 || status=$?
      cat "build/lowfat-controls/$name.log"
      echo "$name: exit=$status"
    done
    /work/build/bin/clang -O0 -g -fsanitize=lowfat \
      build/lowfat-controls/bounds-check.c -o build/lowfat-controls/bounds-check
    build/lowfat-controls/bounds-check
    status=0
    build/lowfat-controls/bounds-check overflow \
      > build/lowfat-controls/bounds-check.log 2>&1 || status=$?
    cat build/lowfat-controls/bounds-check.log
    echo "bounds-check overflow: exit=$status"
  '
```

Validation: the upstream configuration check printed `OK`; the full build and bundled tests passed. All project tests use `-O0 -g -fsanitize=lowfat`.

| Test | Result |
| --- | --- |
| `positive-overflow.c`: write `p[64]` after `malloc(64)` | `ST DONE`, exit 0, not detected |
| `positive-uaf.c` | `ST DONE`, exit 0, not detected |
| Safe access: write `p[0]` after `malloc(64)` | `ST DONE`, normal exit |
| Out-of-bounds access: write `p[128]` in the same program | `LOWFAT ERROR: out-of-bounds error detected!`, exit 134 |

The overflow log reports `operation = write`, `size = 80`, and `overflow = +48`: a 64-byte request receives an 80-byte allocation, so `p[64]` falls in padding while `p[128]` crosses the allocation boundary. Allocation-boundary detection was verified in this container; the two original positive controls did not pass, and the full matrix and performance experiments have not been run.
