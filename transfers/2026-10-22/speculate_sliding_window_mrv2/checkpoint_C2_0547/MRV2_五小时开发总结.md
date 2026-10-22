# MRV2 五小时开发总结

本轮授权窗口为 **2026-10-22 05:04:38–10:04:38 UTC（13:04:38–18:04:38 +08）**。实际于 05:50:02 UTC（13:50:02 +08）完成交付，工作约 45 分钟。当前容器缺少 NPU 设备节点，共享 NFS 也低于预设 500 GiB 水位；设备分支没有安全准入条件。本轮完成可独立进行的 production 修复、固定候选、Host 检查和交付后提前结束。public Graph Gate 保持冻结。

## 起点与资料

接收材料的外置 transfer manifest 与相同 release、task、56 分片及整包身份吻合；原发布校验器因预期包内 manifest 报的 `FAIL` 保留。原 ZIP 7535 个成员、顶层 SHA256SUMS 7511 路径、catalog 7480 路径已做路径集合对账；缺 SHA 覆盖的 24 个成员均是 SHA256SUMS 文件。Repair7 发布 handoff/input pack/报告哈希与给定值一致；受检实际 JSON/JSONL 没有重复键。详情见 `01_接收与源码身份复核.md`、`../state/RECEIVE_AUDIT.json`。接收报告称 `LucianWQZ/private-file-relay` 实际 public，本轮没有向它上传资料，也未更改可见性。

Shell Git 网络受限，因此从服务器已有的干净 Repair6 parent checkout 加归档 Repair7 patch 重建精确 Git 对象，并用 GitHub API 核对提交头：基线 `7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14` / tree `6dd40a67a500480556068be8b6ebcd977e3cc3e8`；vLLM pin `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`。这不是 fresh Git clone。10 个 fixture 文件逐文件哈希吻合，见 `../state/FIXTURE_HASHES.json`。

## 两轮实际修改

1. **C1 production 修复**：`949afbd07c21133cd76cef43365a700cb46de3fb` / tree `9fd864d170666b510eeeac701c01854f0f017202`。旧 Graph proposal 抛错后经 abort 清零 backing；若 replay/UPDATE 已部分提交，设备可能仍读该内存。修复前 Host 反例失败，显示 backing 被重置。修复后有 live inputs 的 Graph 异常保留 lease/backing、禁止继续复用；诊断 driver 识别不确定提交并以 74 隔离子进程。详细代码链与边界见 `02_Graph异常路径修复与剩余合同.md`、`C1_quarantine_change.patch`。
2. **C2 本地候选准入**：`303ef7fe117d372d5f9463d3d79b90e56b9e695d` / tree `a8cdb7a4793022e880bce1e7c591dd30b79f7a94`。旧 PREPARE/BIND/runner 只接受已发布 `VERIFIED`，不能合法运行 C1。新增独立本地 prepare/bind 与 runner 校验，检查 clean commit/tree、Repair7 ancestry、vLLM pin、关键文件/fixture 哈希、Host 结果和 schema；逐 case 设备 receipt 仍为硬条件。C2 明确 `LOCAL_COMMITTED_CANDIDATE`、`REMOTE_PUBLICATION=NOT_PERFORMED`，没有伪造发布事实。见 `03_环境准入与本地候选.md`、`C2_local_admission_change.patch`。

当前开发 HEAD 与最佳本地候选均为 **C2**；两个 Git 工作树和独立候选 checkout 均干净。最新候选包含 C1 production 修复。本轮最近关键设备验证通过候选为 **无**；Repair6 的 Base 10 对、Target4 12 对只可作旧 SHA/旧 Phy-ID8 参考，不能升格为 C2 通过。本轮只本地提交，没有 push、PR 或合并。

## 验证结果与局限

- C1 受影响 Host 回归为 **950 passed、2 failed**。两项失败是上游 AST drift guard，在干净 Repair7 checkout 上单独复测同样失败；不是 C1 新引入。C1 最终异常隔离聚焦 3 项通过，较小范围 75+31 项通过。C2 开发树相关 55 项通过，固定 C2 checkout 的异常隔离 3 项和本地准入 3 项分别通过。未关闭 hooks 或伪称全套检查通过。
- C2 的真实 Host prepare 重新核验 10 个 fixture 文件，生成 **44 case** 计划和 **39 行 CLI→kwargs→Ascend schema** 检查（5 种配置，含诊断开启/关闭），见 `../runs/C2_303ef7fe/local_prepare_01/`。这不是 EngineArgs/平台工厂或模型启动结果。无设备 receipt 的 committed CONFIG runner 返回 `BLOCKED_DEVICE_MAPPING` 且 `device_started=false`；验证了拒绝路径，正向设备准入尚未运行。
- 设备：用户授权 Phy-ID 0–15，但当前容器 `/dev/davinci*` 为空，`npu-smi` 无法使用，逻辑设备至宿主 Phy-ID 映射未知。未运行 probe、真实 CONFIG、P0/A0/A1/B0、A/B/A′ 连续数值、完整 Base/Target4、生命周期 ABORT、正常 profiling 或多卡。模型 worker 的实际 Python/二进制导入来源尚不能核验。详见 `../state/DEVICE_ENVIRONMENT.json`、`../state/C2_CANDIDATE.json`。
- Profiling：本轮四格及控制组均未采集；`MRV2_Profiling分析.md` 与 `MRV2_Profiling_Summary.json` 只列本机 API 能力和旧 Repair5 的明确分版本参考，不给 C2 加速率或设备完成结论。
- 正常成功路径仍在 `retire_generation` 后可能直接 reset backing，缺乏最后 reader completion 合同；UPDATE(N) 作用代际、task 内 operand 和 physical read-set 也未证明。异常隔离修复不关闭这些问题。详细待决项在 `../journal/DECISION_QUEUE.md`。Graph **未达到正式支持审查条件**，public Gate 冻结。历史其他特性矩阵没有从“主要剩 Graph”外推为全部通过。

## 路径、资源与后续最小工作

源码：`../work/vllm-ascend`；固定 C2 checkout：`../candidates/C2_303ef7fe/vllm-ascend`；run 根：`../runs`。`/mnt/share/.../dev/adapt/runs` 在 NFS，`/mnt/wenqing` 在另一本地 ext4 文件系统。“挂载 NPU”指容器设备节点，不是切换这两个数据目录。run 仍选 NFS，因为备用只有约 21 GiB；但 NFS 余量从开始约 1.4 TiB 降至 05:48 的约 203 GiB，已低于 500 GiB 水位，不再产生大型数据。见 `../state/PATH_BINDING.json`、`../state/RESOURCE_PREFLIGHT.json`。本轮没有模型或 profiler 后台进程，也未占用 NPU。

下一轮先获得能看到授权 NPU 节点且能核对真实 Phy-ID 的执行容器，重新记录 boot/namespace/PID/占用/HBM/空间。按 `RESUME.md` 以 C2 clean checkout 完成 committed inspect→probe→check→逐 case local bind，先跑真实 CONFIG/P0/A0/A1/B0 和 NUMERIC_SENTINEL；前哨通过后分 Base/Target4 完整 Target 和正常 profiling 四格/控制组，再查 UPDATE/backing 生命周期。若 NFS 仍低于水位，先解决存储预算，不启动大 tensor/trace 采集。所有 case、新候选和设备段分别裁决；不拿旧结果或 Host 通过代替设备验收。

交付索引见 `../return/DOWNLOAD_MANIFEST.json`。Bundle `../return/MRV2_C2_from_Repair6.bundle` 已从只有 Repair6 parent 的独立仓库恢复到 C2 SHA/tree，见 `../state/BUNDLE_VERIFY_C2.json`；其中不含模型或忽略的安装包二进制文件。恢复方法见 `04_提交与Bundle恢复.md` 和 `RESUME.md`。
