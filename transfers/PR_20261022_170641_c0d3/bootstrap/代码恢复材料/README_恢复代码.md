# 双仓代码恢复说明

## 固定身份

- Ascend：`2604675e520c23740c5225b6af8857eed8bd9391`，tree `afbf69a93f1c7e761769baa9044577d8b83b7a35`。
- vLLM：`a98247ab4db686ee03c66d5feb3c761e52a2f8ab`，tree `7f2a24a827bbbb2f211e02031f9d4d0d556d536c`。
- Ascend 固定 base：`128f35ed1461ecb34bc8b87583a67a66bc4bd1d6`。
- 两个来源工作树在本轮开始与结束均应为 clean；没有 staged、unstaged 或 untracked 补丁需要另行应用。

本目录直接包含已验证的 bundle、shallow 边界、恢复脚本和 `SOURCE_BINDING.json`。这些文件源自 ArchitectureReview 冻结包；本轮复制后重新计算并核对 SHA256。

## 文件

```text
代码恢复材料/
├── SOURCE_BINDING.json
├── bundles/
│   ├── vllm-ascend.bundle
│   ├── vllm-ascend.shallow
│   ├── vllm.bundle
│   └── vllm.shallow
└── tools/
    ├── restore_sources.py
    └── server_preflight.py
```

`restore_sources.py` 必须与 `server_preflight.py` 位于同一目录。只带前者会触发 `ModuleNotFoundError`；这属于明确依赖缺失，不是 bundle 损坏。

## 服务器恢复命令

假设完整包解压到：

```bash
TASK_ROOT=/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/PR_服务器开发交接_20261022_170641_0800_c0d3
RESTORE_ROOT=/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/pr.restore-$(date +%Y%m%d-%H%M%S)

python3 "$TASK_ROOT/代码恢复材料/tools/restore_sources.py" \
  --input-root "$TASK_ROOT/代码恢复材料" \
  --owned-root "$RESTORE_ROOT" \
  --binding "$TASK_ROOT/代码恢复材料/SOURCE_BINDING.json"
```

恢复脚本要求目标目录不存在，以免覆盖未知工作。恢复完成后：

```bash
git -C "$RESTORE_ROOT/src/vllm-ascend" rev-parse HEAD
git -C "$RESTORE_ROOT/src/vllm-ascend" rev-parse 'HEAD^{tree}'
git -C "$RESTORE_ROOT/src/vllm-ascend" status --porcelain=v2 --branch
git -C "$RESTORE_ROOT/src/vllm-ascend" fsck --full

git -C "$RESTORE_ROOT/src/vllm" rev-parse HEAD
git -C "$RESTORE_ROOT/src/vllm" rev-parse 'HEAD^{tree}'
git -C "$RESTORE_ROOT/src/vllm" status --porcelain=v2 --branch
git -C "$RESTORE_ROOT/src/vllm" fsck --full
```

期望两个 checkout 均 detached、clean、SHA/tree 精确匹配，且 `.git/objects/info/alternates` 不存在。

## 已做的恢复验证

本轮先从复制后的原始 ArchitectureReview payload 恢复一次，验证 SHA/tree、clean、`git fsck --full` 和 no-alternates。最终完整 ZIP 生成后，校验器还会从 ZIP 实际成员提取本目录，再做第二次恢复；最终结果见 `校验结果/PACKAGE_VERIFICATION.json`。

## 外部依赖

bundle 不包含以下对象：

- `csrc/third_party/catlass` gitlink `41bf90da655bba3c66d0acd7e00abe33960ecfd6`；服务器须从 `https://gitcode.com/cann/catlass.git` 或可信镜像取得精确提交。
- CANN、driver/firmware、Python、torch、torch_npu、triton-ascend、native wheel/编译产物。
- 模型权重、checkpoint/config、团队性能工具与 A3 资源授权。

Mac venv 和 Mac 编译产物不能作为 A3 runtime。服务器应在 `dev/pr/env` 记录完整依赖和 native/import 身份。

## 历史边界

两个 bundle 使用已哈希的 shallow 文件表达有意缺失的父历史，足以恢复固定 checkout 并继续开发。它们不是边界以前的完整 Git 历史。不要删除 shallow 文件来伪装完整历史；需要更早来源时按 `EXTERNAL_DEPENDENCIES.json` 读取已有 MRV2 档案。
