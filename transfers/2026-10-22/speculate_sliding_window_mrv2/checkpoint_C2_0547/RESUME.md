# 下一会话恢复

本轮 session `20261022T050438Z` 从 **2026-10-22T05:04:38Z** 起算，原设备授权窗口截止 **2026-10-22T10:04:38Z**。不要因重启会话重新起算 5 小时；如果已过期，先取得新的资源窗口。先读 `../journal/00_当前进展.md`、`MRV2_五小时开发总结.md`、`../journal/DECISION_QUEUE.md`，再看 `../state/SESSION_STATE.json` 和本文件；无需重读 7535 个历史文件。

当前开发分支 HEAD 与最佳本地候选：C2 `303ef7fe117d372d5f9463d3d79b90e56b9e695d` / tree `a8cdb7a4793022e880bce1e7c591dd30b79f7a94`。固定源码目录 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/C2_303ef7fe/vllm-ascend`，固定 vLLM `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/C2_303ef7fe/vllm`，run 根 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs`。C2 仅本地提交，`REMOTE_PUBLICATION=NOT_PERFORMED`，设备未验证。现有 C2 Host plan 在 `runs/C2_303ef7fe/local_prepare_01/case-plan.json`，状态为本地固定候选且无设备 receipt。两组固定 checkout Host 测试各 3 项通过，39 行 schema-only 配置有效；真实 EngineArgs/模型未运行。

当前阻塞：本容器无 `/dev/davinci*`，`npu-smi` 不可用，Phy-ID 映射未知。用户授权的是宿主 Phy0–15，不是当前容器任意逻辑 `npu:0`。切换数据目录或用 aisbench 客户端不能提供设备节点。NFS 空间 05:48 已降至约 203 GiB，低于 500 GiB 水位；没有充足新鲜预算时不运行大 tensor/trace。

## 恢复前检查

1. 核对 UTC 时间、原授权是否仍有效、平台是否实际提供可用的执行容器。记录 hostname、boot ID、PID/namespace、设备节点 major/minor、可见设备变量、`npu-smi`、现有进程/HBM/健康与真实逻辑→宿主 Phy-ID。保存为新的 device segment，不能复用旧 Phy-ID8 映射或 owner receipt。
2. 检查 NFS 与备用 ext4 的实际空闲、inode、Host RAM、HBM、单样本 Target/trace 的最大预计写入和临时空间；共享增长可能使旧 `RESOURCE_PREFLIGHT.json` 过期。不要删除历史输出。
3. `git -C <C2源码> rev-parse HEAD HEAD^{tree}` 和 `git status --porcelain --untracked-files=all` 必须与上文一致且干净；vLLM pin 为 `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`。重新核对 `_build_info.py`、两个忽略的二进制扩展来源/哈希，见 `../state/C2_CANDIDATE.json`；安装包 donor 的 ABI 与实际 worker import 尚未验证。worker 子进程也须记录 import 源，不只主进程。
4. 保持 torch_npu/CANN/驱动/vLLM pin，不修改共享代理或全局配置。已完成 Host 工作可按源码影响分析引用；设备结果须按 C2/新 device segment 重跑。

## 设备准入与 case

先用 committed `tools/p7x_graph_repair7_device.py --help` 核对参数。`inspect` 只读；确认实际映射与授权范围后，按 `inputs/DEVICE_ADMISSION.md` 完成最小 probe 自身宿主/容器 PID 关联和 committed `check`。不要仅凭用户授权构造管理员/owner 签名，receipt 必须含真实可核对的机器映射、资源占用、时效与进程证据。当前 C2 TP1 plan 只准入 0–7；后 8 芯片的全卡扩展须另建 topology/config/device segment 和新鲜可用性证据。

C2 使用 committed `tools/p7x_graph_local_candidate.py bind`，而不是发布候选专用的 input pack `BIND_DEVICE.py`。将上文 C2 plan、单 case ID、新鲜该 case receipt、**全新** admitted plan 输出路径传给 `bind`；成功后再用 committed `tools/p7x_graph_repair6_runner.py --plan <admitted-plan> --case-id <case> --output <全新attempt执行根>` 执行。每个 case/attempt 独立目录，先 `CONFIG`、P0、A0/A1/B0，再 `NUMERIC_SENTINEL`；通过后 Target4 12 场景和必要 Base/Target 双臂、生命周期、正常四格 profiling/控制组。`CONFIG` schema 成功不等于 EngineArgs/平台工厂/模型成功。

无 receipt 的 CONFIG runner 已在本轮返回 `BLOCKED_DEVICE_MAPPING`、`device_started=false`；这是有意拒绝，不应通过改 `publication_status` 或跳过 source/admission 检查解决。若 C2 plan/Host evidence/fixture stat 改变，重新用全新输出目录运行本地 `prepare`；不覆盖 `local_prepare_01` 或旧 attempt。C2 的准入工具仍未在真实设备上正向验证。

`NORMAL_UPDATE_GENERATION`、`NORMAL_BACKING_REUSE`、task 内 operand 和 physical read 的平台合同仍在 `../journal/DECISION_QUEUE.md`。成功路径 Host retire/reset 不能作设备 completion 证据；串行诊断同步须单列，不可当正常重叠路径证明。未知 native 部分提交只做允许的 Host 错误导出与子进程隔离，不继续 KV 恢复或正常复用。public Graph Gate 保持冻结。

## Bundle 与输出

`../return/MRV2_C2_from_Repair6.bundle` 以 Repair6 `fd0716c59562f64262672de12e4ae26259908d0b` 为 prerequisite；从仅有该 parent 的独立 checkout `git bundle verify` 和 fetch 已恢复 C2 SHA/tree，见 `../state/BUNDLE_VERIFY_C2.json`、`04_提交与Bundle恢复.md`。Bundle 不含模型、ignored 生成文件或二进制 donor。大 raw 继续留在 `runs`，review ZIP 只含小型报告/摘要。`../return/DOWNLOAD_MANIFEST.json` 提供 bytes/SHA256。
