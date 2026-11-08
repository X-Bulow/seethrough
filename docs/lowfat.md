# LowFat 构建尝试

- 日期：2026-11-07；记录人：C。
- 环境：实验室 VirtualBox Ubuntu 26.04 x86-64；glibc 2.43；GCC/g++ 15.2.0；CMake 4.2.3。
- 上游：https://github.com/GJDuck/LowFat
- commit：`20f8075dd1fd6588700262353c7ba619d82cea8f`。
- 在项目根目录执行的构建命令：

```bash
mkdir -p build &&
git clone https://github.com/GJDuck/LowFat build/LowFat &&
(
  set -o pipefail
  cd build/LowFat &&
  git rev-parse HEAD | tee commit.txt &&
  bash build.sh 2>&1 | tee build.log
)
```

构建日志摘录：

```text
build.sh: using the default LowFat configuration (sizes.cfg 32)...
build.sh: warning: one or more of clang-4.0/clang++-4.0/llvm-config-4.0 is not installed!
build.sh: will try gcc.
build.sh: checking the CPU...[bmi][bmi2][lzcnt]
build.sh: building the LowFat config builder...
build.sh: building the LowFat config...
build.sh: building the LowFat config check...
build.sh: checking the LowFat config...
build.sh: ERROR: configuration check failed!
error: joinid offset (0x628) is wrong!
```

[上游配置生成器](https://github.com/GJDuck/LowFat/blob/20f8075dd1fd6588700262353c7ba619d82cea8f/config/lowfat-config.c)
将 `LOWFAT_JOINID_OFFSET` 固定为 `0x628`；
[配置检查程序](https://github.com/GJDuck/LowFat/blob/20f8075dd1fd6588700262353c7ba619d82cea8f/config/lowfat-check-config.c)
在线程 detach 后读取该偏移，并检查其值是否等于线程自身。当前环境未满足这一内部线程布局假设；实际可用偏移未调查。

结论：本轮原版 LowFat 构建在配置检查阶段失败，未进入后续 LLVM 构建及项目 `corpus/controls/` 测试，不能评价检测能力。按任务清单降为 P2，本轮不继续投入；不修改上游源码，不跳过检查。本结果仅适用于上述 commit 和环境。
