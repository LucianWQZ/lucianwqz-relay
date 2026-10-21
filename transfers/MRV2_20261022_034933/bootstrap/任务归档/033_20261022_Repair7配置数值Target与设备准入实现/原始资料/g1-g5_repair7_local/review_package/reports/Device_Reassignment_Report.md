# Repair6 Device Reassignment Report

## 1. 结论

- 用户分配的合法范围：宿主机 **Phy-ID 0–7**。
- 旧 campaign 使用 `ASCEND_RT_VISIBLE_DEVICES=8`，实际落到 **NPU4 / Chip0 / Phy-ID8**，不在合法范围。
- 2026-10-21 17:26 UTC 左右已停止后续 NPU 启动；B2 旧设备子进程已终止并保留 partial。
- 尝试新环境 `ASCEND_RT_VISIBLE_DEVICES=0` 后，torch_npu 看到 `device_count=1`、`current_device=0`，但实际设备表仍显示 **NPU4/Chip0/Phy-ID8**。因此当前容器只映射后 8 个芯片（或不支持从前 8 个中选择），不能仅通过环境变量完成纠正。
- 没有 reset 设备、没有 kill 无关进程、没有修改源码/模型/Graph/checker。
- 在所有 NPU 进程退出后才做上述结论；后续没有启动新模型。

## 2. 已完成但属于旧设备段的结果

以下结果保留，**标记为 old-device segment，不作为合法 Phy-ID0–7 的新设备正式证据**：

- P0
- A0 / A1 / B0
- PREFIX_OFF / PREFIX_ON
- G4F_OFF / G4F_ON / G4F_COMPARE
- TARGET4_OFF / TARGET4_ON / TARGET4_COMPARE
- NORMAL_ORDER
- B1

其中：

- G4F_OFF/ON：各 10 个 `CAPTURED_COMPLETE` + 1 个 `CAPTURE_BUCKET_ABSENT: target (4,32)`；Base expected OPEN。
- G4F_COMPARE：10/10 complete pairs PASS；第 11 个 `EXECUTION_FAILED`，整体 `PARTIAL_PREFIX_VALID`。
- TARGET4_OFF/ON：12/12 `SAMPLE_COMPLETE`，`SINGLE_ARM_STRUCTURE_VALID`。
- TARGET4_COMPARE：12/12 pairs PASS，hidden/logits `max_abs=0`、finite，`SAMPLE_COMPLETE`；但 `campaign=REQUIRES_EXTERNAL_EXECUTION_JOIN`，不能单独当成完整 campaign PASS。
- NORMAL_ORDER：`OBSERVED_NORMAL_ORDER_NOT_REUSE_PROOF`，请求 joint PASS；normal reuse/effective generation UNPROVEN。
- B1：请求与 joint PASS；完整 16-token 输出。
- B2：旧设备上启动后被资源纠正终止，`returncode=143`（受控 TERM），campaign/partial 保留，joint FAIL；**不是数值失败，也不是新设备结果**。

## 3. NUMERIC_TARGET4

在旧设备上、模型加载前失败：

```text
ValidationError: VllmConfig
draft_window_graph_numeric_diagnostic
Unexpected keyword argument
```

- producer 最先失败；checker 因没有 `numeric-reference.json`/`controlled-target.json` 返回 `INVALID_EVIDENCE`。
- 这是 submitted config 与 pinned vLLM `VllmConfig` 的契约问题，不是资源不足，也不是已确认的模型数值不一致。
- 未用新卡盲目重跑同一失败。换卡不能解决该配置错误。

## 4. 设备映射证据

### 4.1 npu-smi 表

容器内 `npu-smi info -m`:

```text
Chip Logic ID == Chip Phy-ID: 0..15
NPU 0 Chip0 -> Logic 0 / Phy 0
...
NPU 4 Chip0 -> Logic 8 / Phy 8
...
NPU 7 Chip1 -> Logic 15 / Phy 15
```

合法范围应为上表 Phy-ID 0–7（NPU0–NPU3）。

### 4.2 旧环境

```text
ASCEND_RT_VISIBLE_DEVICES=8
torch_npu program device npu:0
actual host process: NPU4 / Chip0 / Phy-ID8
```

### 4.3 新尝试环境

创建 `runtime/env_repair6_phy0.sh`：

```bash
source runtime/env_repair6.sh
export ASCEND_RT_VISIBLE_DEVICES=0
```

最小只读/轻量 probe 结果：

```text
ASCEND_RT_VISIBLE_DEVICES=0
torch_npu.npu.device_count()=1
torch_npu.npu.current_device()=0
actual npu-smi: NPU4 / Chip0 / Phy-ID8
```

结论：当前容器把可见 logical 0 映射到 host Phy-ID8；不能在容器内通过改变量选择 host Phy-ID0–7。

### 4.4 当前进程状态

- B2 子进程组已 TERM；launcher `returncode=143`，runner `EXECUTION_FAILED`，没有进程残留。
- 最小 probe 已正常退出；没有本 campaign 的模型进程。
- npu-smi 的 NPU4–7 仍有其他 PID（非本 campaign），未终止。
- NPU0–3 当前没有本 campaign 进程。

## 5. 环境差异与 hash

| 文件 | bytes | SHA256 |
|---|---:|---|
| 原 `runtime/env_repair6.sh`（旧 die8） | `stat` | `7d5517a073853e2cb1e3eb061e5708d7ce45f1ecee8c227741e28baa7a351d12` |
| 新 `runtime/env_repair6_phy0.sh` | `stat` | `6c2008ef46e9a826046a3714c69b03ac19ab2c2b0575ecddbc1fefd9cdf3ca83` |

新文件只覆盖设备变量，不修改源码/模型/Graph；但已证明该 override 不能改变容器到 host Phy-ID 的映射。

## 6. 最小容器调整方案

需要平台/容器维护者将容器设备映射改为 host Phy-ID 0–7，而不是仅改 `ASCEND_RT_VISIBLE_DEVICES`：

- 让容器内第一个 Ascend device node 对应 host `/dev/davinci0`（Phy-ID0），或
- 显式 expose host Phy-ID0–7 的 8 个设备节点并保证容器内 logical 0–7 与之一一对应；
- 保留 `/dev/davinci_manager` 与所需 capabilities；
- 重新启动容器后，用 `npu-smi info -m` 与一个小张量 probe 复核 process 落在 Phy-ID0–7。

在容器映射修正前，任何设置 `ASCEND_RT_VISIBLE_DEVICES=0..7` 都可能仍落到后 8 个芯片，禁止启动模型。

## 7. 保留/补跑策略

- 当前旧设备完成的大 Target 双臂/比较/锚点保留，不重跑为“新设备结果”；最终报告明确 segment。
- 由于容器映射未修正，本轮无法在新合法设备补跑 A0/A1/B0 或 profiling；这些状态记为 `BLOCKED_DEVICE_MAPPING`，不是代码失败。
- 换卡后最小锚点：P0 → A0/A1/B0；随后只在合法设备上补做被阻断的 B2/O0/O1/C2/LIFE/ABORT/自然 G4/profiling；旧设备完整 Target 结果不因换卡无理由重跑。
- 所有新 attempt 使用新 runner 输出根，不覆盖 attempt1。

## 8. 资源

- `/mnt` 当前剩余约 21 GiB（随 artifact 变化）。
- 已完成 artifacts 约数 GiB；完整 Target chunk store 有去重/压缩，实际占用低于声明预算。
- 未删除失败证据；Repair5 旧 20G controlled 目录已移至 `/mnt/share/wenqing/repair5_evidence_archive/...` 并在原路径留 symlink，保留可解析映射。
- 打包前会重新测峰值空间；不足只阻断受影响分支。

## 9. 禁止事项复核

- 未修改已发布 production/producer/checker。
- 未修改模型参数、Window 数学、Graph 顺序、源码 SHA。
- 未 reset 设备、未抢卡、未 kill 无关进程。
- 未把旧设备结果写成新设备 PASS。
- 未解冻 public Graph。
