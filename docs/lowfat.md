# LowFat 构建与验证

环境：实验室 VirtualBox VM 内的 Ubuntu 18.04 Docker 容器，glibc `2.27-3ubuntu1.6`；生成的编译器为 clang 4.0.0。
上游：https://github.com/GJDuck/LowFat；commit：`20f8075dd1fd6588700262353c7ba619d82cea8f`。

在项目根目录构建（需要 Docker；以下目录和容器名尚未存在）：

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

编译器路径：容器内 `/work/build/bin/clang`。构建日志：`build/LowFat-ubuntu18/build.log`。

在宿主 Ubuntu 中创建边界验证程序：

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

在同一容器环境中编译并运行原有 controls 和边界验证程序：

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

验证结果：原版配置检查输出 `OK`，完整构建及自带测试通过。项目测试均使用 `-O0 -g -fsanitize=lowfat`。

| 测试 | 结果 |
| --- | --- |
| `positive-overflow.c`：`malloc(64)` 后写 `p[64]` | `ST DONE`，exit 0，未检测 |
| `positive-uaf.c` | `ST DONE`，exit 0，未检测 |
| 安全访问：`malloc(64)` 后写 `p[0]` | `ST DONE`，正常退出 |
| 越界访问：同一程序写 `p[128]` | `LOWFAT ERROR: out-of-bounds error detected!`，exit 134 |

越界日志报告 `operation = write`、`size = 80`、`overflow = +48`：64 字节请求实际分配为 80 字节，`p[64]` 位于填充空间，`p[128]` 超出分配边界。已验证该容器中的分配边界检测；两个原有 positive controls 未通过，完整矩阵和性能实验尚未运行。
