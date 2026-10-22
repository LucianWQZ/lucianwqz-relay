# MRV2 非 Graph PR 服务器开发交接摘要

## 一句话结论

推荐从现有 `2604675…` 候选继续并对已证问题做定点重构，当前不需要从 base 重写。代码和配套 vLLM 可恢复，但候选仍为 `ARCHITECTURE_LOCAL_REVIEW=BLOCKED`，该 SHA 没有 A3 或性能结果，完整非 Graph 范围未验收。

## 1. 最终目标与仍待明确的边界

最终目标是把 MRV1 Draft Sliding Window 迁移到 MRV2，并交付非 Graph 基础与适用叠加：Eagle3、DFlash、eligible DSpark；MTP 与确认的共训 DeepSeek-V4 DSpark forced-OFF；FlashComm/SP、DSA-CP、Async、prefix cache、chunked prefill、多请求/混合到达、真实生命周期；GLM/千问所需 backend、multi-gid 与并行组合；A3 correctness 和 GLM TP16 性能。Draft Window Graph 独立推进，但共享修改要回归已有 Target Graph、MRV1 和 OFF。

仍待明确：共训 V4 checkpoint/config 身份；plain Eagle/DFlash2/dynamic-K 产品范围；required compressed/SFA/indexer/multi-gid 模型；legacy DSA-CP 的可支持路线；A2/A5/310P 范围。

## 2. 当前真实代码身份

- CURRENT_HEAD / RECOMMENDED_START / LATEST_REMOTE_VERIFIED：Ascend `2604675e520c23740c5225b6af8857eed8bd9391`，tree `afbf69a93f1c7e761769baa9044577d8b83b7a35`。
- paired vLLM：`a98247ab4db686ee03c66d5feb3c761e52a2f8ab`，tree `7f2a24a827bbbb2f211e02031f9d4d0d556d536c`。
- fixed Ascend base：`128f35ed1461ecb34bc8b87583a67a66bc4bd1d6`。
- 工作树：本轮只读核实时两个仓均 clean；没有发现 2604675 后续生产提交。
- 远端诊断 ref：`test/mrv2-draft-window-nongraph-a3-diagnostic-20261021-2604675e520c` 曾独立 fetch 核验。远端事实只证明对象可取，不证明功能 CI/A3。

`LAST_DEVICE_TESTED` 与 `LAST_PERFORMANCE_TESTED` 不是当前 SHA。现有历史设备/性能材料均为 `REPORT_ONLY`，必须按其旧源码/overlay/模型/环境理解；当前 SHA 的 A3/性能是 `NOT_RUN`。

## 3. 为什么局部重做而不是从头开始

现有候选已经包含可复用且有 Host/source 证据的 policy、窗口数学、FullSource/read-view 隔离、方法接入、K/K+1 capacity 修复、Eagle step-0 修复、lifetime owner 和大量 targeted tests。它相对 fixed base 的变更集中在 39 个文件，架构问题可以定位到 exact-length consumer、部分 provider 和设备 completion 边界。没有证据表明 runner 主链或全部设计不可收敛，因此结论为 `CONTINUE_WITH_TARGETED_REWORK`。

## 4. 最新代码实际完成了什么

实际源码完成：

- Window policy、OFF/forced-OFF 和 unsupported-on rejection。
- `H/E/S/V` 数学、canonical Full owner 与 per-gid Draft read view。
- Eagle3、DFlash、DSpark 接入及 Host 合同。
- DSpark K/K+1 sparse-index capacity 与 lazy buffer 边界修复。
- Eagle replicated PCP step-0 metadata 重复构建修复。
- DSpark/no-DCP/ordinary MLA 复用当前 preparation exact pair，去掉 Window 重复 copy，保留基线 copy。
- legacy DSA-CP 不可达扩展撤回并保留显式 unsupported。
- factory callback LIFO/冲突/异常恢复与 owner Host 测试。

只有历史报告或尚未设备证明：A3 native correctness、实际 TP16/EP/FlashComm/SP、full engine Async、自然 pressure、prefix/chunked/mixed real serving、multi-gid/复杂 backend、完整 Full-write/Target、性能。

## 5. 官方架构与风格问题

固定 MRV2 design 要求 persistent state 与 per-step input 分离、async-first、避免 CPU synchronization。候选在 Eagle/GQA/DFlash 等路径仍为 Window 规划获取 current exact 的 CPU snapshot，并且后续 builder 有 CPU list/chunk consumer；只把 projection 搬到设备不能解决同步。此项是 A01 `ARCHITECTURE_BLOCKED`。

共享 `dsa_v1.py`/Triton indices/factory 修改需要明确 OFF、MRV1、warmup/profile、已有 Graph 影响。legacy DSA-CP 仍由 base guard 拒绝，PCP 不是替代。所有新分配/owner/callback 要说明生命周期、线程/流假设和最后 reader 完成。

## 6. A3、性能与完整覆盖进度

- 当前候选 A3：`NOT_RUN`。
- 当前候选性能：`NOT_RUN`。
- 完整非 Graph：`NO`。
- 诊断材料具备 39-case 索引和部分入口，但不是 39 条都可执行；模型、资源、native、driver、team CLI 仍需现场绑定。
- 历史 GLM 8 单元为十进制输入 `16000/32000/64000/128000` × OFF/W1024、输出 2000；历史结果不能继承。

## 7. 哪些工作被后续任务替代

- `b013719…` 被架构审查候选 `2604675…` 替代作为推荐源码；后者包含 DSpark capacity、Eagle step-0、exact-pair 和 legacy CP 收敛修复。
- ArchitectureReview 中“Gitleaks/shellcheck 未闭合”被后续 DiagnosticRelease 的隔离工具安装与完整 `bash format.sh ci` PASS 替代。
- ArchitectureReview 的“未发布”被 DiagnosticRelease 的单 ref push 与独立 fetch PASS 替代。
- 上述替代不改变 A01 BLOCKED、A3 NOT_RUN、性能 NOT_RUN 或完整范围缺口。

## 8. 代码和材料能否离线恢复

本交接已直接包含双仓 bundle、声明的 shallow boundary、hash 和恢复脚本；本轮已在独立目录核对 HEAD/tree/clean/fsck/no-alternates，最终还会从完整 ZIP 实际成员再恢复一次。恢复验证只证明源码对象与必要工作树状态可得，不证明环境、native ABI、模型或 NPU 功能。已有约 30 GB MRV2 历史档案是外部依赖，不重复纳入本 PR 包；服务器接收状态目前按用户提供记 `USER_REPORTED`，待未来读取回执确认。

## 9. 服务器第一件事

先完成无设备恢复和固定 runtime/native ABI 身份。第一个有界问题是 DW-A01：核实现有 exact-length consumer 和算子 schema，做最小 native 调用、动态 device length 数值与短 trace，区分 Window 新增 D2H、基线 copy、builder `.tolist` 和 observer 开销。形成逐 consumer 事实表后，再选择最小局部实现或必要的上游接口提案。不能用 upper、旧 generation 或伪 non-blocking copy。

## 10. 下一轮 GitHub 发布仍需要什么

本轮不 push、不上传。未来生产修改形成新 SHA/tree 后，需要重新绑定 Host/device/server input、检查敏感内容、完整 prepush、单 ref push 与独立 fetch。资料中转仓 `LucianWQZ/private-file-relay` 的名称不证明私有；本轮 2026-10-22 以只读 GitHub API 确认该仓库 `visibility=public`。发布前必须重新只读确认当时可见性，并按资料敏感性决定方式，不能自动沿用旧 manifest 的“私仓”措辞。

## 外部审阅建议

先读本文件、`01_最终需求与验收范围.md`、`03_代码起点裁决.md`、`04_架构兼容与待解决问题.md`、`CODE_STATE.json` 与 `NEXT_SESSION_HANDOFF.json`。需要挑战某项结论时，再按 `DOCUMENT_CATALOG.jsonl` 索取对应原始 finding、测试 log 或源码片段；不要求上传完整大包。
