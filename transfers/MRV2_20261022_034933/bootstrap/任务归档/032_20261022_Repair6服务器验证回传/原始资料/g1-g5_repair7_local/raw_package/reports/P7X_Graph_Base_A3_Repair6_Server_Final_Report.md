# P7-X MRV2 Draft Sliding Window — Node101 Ascend A3 Repair6 服务器最终报告

- RUN_ID：`20261021T071630Z_fd0716c5`
- RUN_ROOT：`/mnt/wenqing/mrv2_graph_repair6_verify/20261021T071630Z_fd0716c5`
- 最终源码：`fd0716c59562f64262672de12e4ae26259908d0b`
- tree：`125b29bcb8fe501d69b53e185f9ec89075528310`
- parent：`febc43be3309f6d2cd87f9332cb7e031ebaad001`
- pinned vLLM：`84030bbe3d74d99bad477a3d2e37a973ccd8865c` / tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`
- Python 3.11.10；torch 2.10.0+cpu；torch_npu 2.10.0.post4；CANN 9.1.0
- public Graph Gate：`STILL_FROZEN`

## 0. 重要边界：设备重分配

用户中途给出最高优先级资源纠正：

- 合法 host Phy-ID 范围是 **0–7**；
- 旧 campaign 的 `ASCEND_RT_VISIBLE_DEVICES=8` 实际使用 **NPU4/Chip0/Phy-ID8**，不在合法范围；
- 已立即停止后续 NPU 启动并释放本任务旧设备进程；
- 尝试 `ASCEND_RT_VISIBLE_DEVICES=0` 后，torch 看到 `current_device=0`，但实际仍落在 **NPU4/Chip0/Phy-ID8**；
- 因此当前容器把可见 logical 0 映射到 host Phy-ID8，**不能仅靠环境变量切换到 Phy-ID0–7**；
- 容器需要重新映射设备；在修正前停止所有新模型，继续安全的 CPU 分析。

因此本报告分为：

- **旧设备段**（Phy-ID8）：已完成的锚点、Target 两臂、比较等；
- **新合法设备段**（Phy-ID0–7）：**没有执行**，被 `BLOCKED_DEVICE_MAPPING` 阻断；
- 两者不能合并成同一物理设备 PASS。

详细证据：`reports/Device_Reassignment_Report.md`、`reports/device_reassignment.json`。

## 1. 最终状态摘要

```text
FINAL_SOURCE = fd0716c59562f64262672de12e4ae26259908d0b / 125b29bcb8fe501d69b53e185f9ec89075528310
PUBLICATION = VERIFIED
SOURCE_IMPORT_FIXTURE = PASS
A0/A1/B0 = PASS / PASS_EXPECTED_NEGATIVE / PASS (old Phy-ID8 segment)
PREFIX_STORAGE = PASS (old Phy-ID8 segment)
FULL_TARGET_BASE = PARTIAL_PREFIX_VALID (10/10 complete pairs PASS; (4,32) expected BLOCKED)
FULL_TARGET_TARGET4 = SAMPLE_COMPLETE (12/12 samples; 12/12 pairs PASS zero tolerance; old segment; external join required)
REAL_MRV2_CONTINUOUS = INVALID_EVIDENCE (VllmConfig config contract; no model load)
ABA_DISCRIMINATION = BLOCKED_DEVICE_MAPPING
NORMAL_ORDER = OBSERVED_NORMAL_ORDER_NOT_REUSE_PROOF
NORMAL_UPDATE_GENERATION = UNPROVEN
NORMAL_PATH_REUSE = UNPROVEN
LIFE = BLOCKED_DEVICE_MAPPING
ABORT = BLOCKED_DEVICE_MAPPING
PROFILING_COLLECTION = BLOCKED_DEVICE_MAPPING
PROFILING_RANGE_COVERAGE = BLOCKED_DEVICE_MAPPING
PROFILING_CORRELATION = BLOCKED_DEVICE_MAPPING
TASK_INTERNAL = OPEN
PHYSICAL_READ = OPEN
BASE_G1_G5_VERIFIED = NO
PUBLIC_GRAPH_GATE = STILL_FROZEN
SERVER_PACKAGE_INTEGRITY = VERIFIED
RECEIVER_INTEGRITY = NOT_YET_VERIFIED
NEXT_ACTION = CONTAINER_DEVICE_REMAP_AND_NUMERIC_CONFIG_FIX
```

## 2. 发布、源码、导入与 fixture

- handoff：`P7X_Graph_Base_A3_Repair6_Server_Handoff.json`，bytes 276,080，SHA256 `9ed64f7f0788c4a15b7850f3d252d72f0ce5274703fe0688fab1ac4298442ef4`。
- input pack：bytes 76,403，SHA256 `6fcf372b12a73ab75845b003c1ca5c4caa4b95ea4f9d5c2d7b2327b57794b7d9`；26 个成员 SHA256SUMS 全通过；包内外 handoff 字节一致。
- publication：`VERIFIED`；clean room：`VERIFIED`；PREPARE 前 `new_sha_device_verification=NOT_RUN`。
- GitHub 独立 clone：commit/tree/parent、pinned vLLM commit/tree、两仓 clean 均匹配。
- handoff 的 24 个 tool/production 诊断 hash 全部匹配；`PREPARE.py` 成功生成 42-case plan。
- fixture manifest：`1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4`；10/10 文件匹配。
- overlay：619 个 Python 文件来自精确 fd0716c5，1269 个非 Python 文件来自本机 A3 donor；没有修改 Git 源码。`source_patch_applied=false`。
- 实际 import：`vllm` 精确 `src/vllm`；`vllm_ascend` overlay 的精确 Python 文件；native `.so` 来自 donor。

证据：`reports/SOURCE_IDENTITY.json`、`reports/ENVIRONMENT_FACTS.json`、`runtime/build_overlay.sh`、`runtime/site/sitecustomize.py`。

## 3. 计划与执行边界

`PREPARE.py` 生成的 `plans/attempt1/case-plan.json` 包含 **42** 个 case；计划明确：

- required：P0/A0/A1/B0、PREFIX_OFF/ON、G4F_OFF/ON/COMPARE、TARGET4_OFF/ON/COMPARE、NUMERIC_TARGET4、NORMAL_ORDER；
- conditional：LIFE、四个 ABORT、PROFILE_ON_long_detailed；
- historical/conditional：C2、自然 G4、B1/B2/O0/O1、profiling 等；
- 42 case / 136 argv 只是 Host 参数解析，不是设备实验。

实际执行 **15 个旧设备 case**，然后 B2 被终止，NUMERIC_TARGET4 在模型加载前配置失败；其余 **26 个** 因设备映射被阻断。

42-case 逐项状态：`reports/Case_Status.json`、`Case_Status.csv`、`commands/Execution_Ledger.jsonl`、`progress/status.log`。

## 4. 旧设备段成功证据

### 4.1 P0/A0/A1/B0

- P0：capabilities；`EXECUTION_APIS_AVAILABLE`，native semantics 未证明。
- A0：Window OFF；1/2/4 批次全部 16 tokens；joint PASS。
- A1：`GRAPH_FROZEN` NotImplementedError；expected negative；不是资源失败。
- B0：21 generations；132 events、120 operand_events、21 G4、147 lifecycle；replay `(1,7)/(2,14)/(4,28)` 各 7 次；105 update、21 retire；joint PASS。
- B0 的 None-return 合同：`OUTPUT_NOT_CAPTURED` / `GRAPH_MANAGER_RETURNS_NONE`，无伪造 hash。
- B0 的 task/physical/completion 仍 OPEN。

### 4.2 PREFIX

PREFIX_OFF/ON 均：

```text
PREFIX_STRUCTURE_VALID_NOT_CAMPAIGN_PASS
samples = [SAMPLE_COMPLETE]
```

单样本实际 chunk store：OFF/ON 约 182–183 MiB，chunk manifest 与 sample 状态成立；这是存储/预算预检，不是完整 campaign PASS。

### 4.3 G4F Base

- G4F_OFF/ON 各 11 个声明样本：
  - 10 个 `CAPTURED_COMPLETE`；
  - 第 11 个 `BLOCKED`，理由 `CAPTURE_BUCKET_ABSENT: target (4,32)`。
- 这是 Base 合同的 expected OPEN；不得写成 Base 全样本 PASS。
- G4F_COMPARE：10 个 complete pairs **全部 PASS**，第 11 个 `EXECUTION_FAILED`，整体 `PARTIAL_PREFIX_VALID`；`campaign=INCOMPLETE_COVERAGE`。

### 4.4 TARGET4 独立扩展

TARGET4_OFF/ON 均 12/12 `CAPTURED_COMPLETE`：
A/B/A_prime/short/long/boundary/nonaligned/mixed/padding/return-short/three-active-four-padded/four-active。

TARGET4_COMPARE：

```text
status = SAMPLE_COMPLETE
complete_pairs = 12
pairs = 12/12 PASS
hidden max_abs = 0.0
logits max_abs = 0.0
```

这是本 campaign 最强的受控 Target 证据：

- 单臂结构有效；
- 12/12 paired numeric 零容差；
- 但 `compare-target` 的 `campaign` 字段是 `REQUIRES_EXTERNAL_EXECUTION_JOIN`，不能单独写成完整 campaign PASS；
- 仍是 **old Phy-ID8 segment**，不是合法 Phy-ID0–7 的新设备证据；
- 不能由 Target4 推导 Base `(4,32)` 已支持。

### 4.5 NORMAL_ORDER / B1

- NORMAL_ORDER：`OBSERVED_NORMAL_ORDER_NOT_REUSE_PROOF`；请求 joint PASS；normal reuse/effective generation UNPROVEN。
- B1：11 组请求全部 16 tokens；joint PASS。
- B2：旧设备段启动后被资源纠正终止，`returncode=143`，campaign/partial/joint 保留；不是数值失败，也不是新设备结果。

## 5. NUMERIC_TARGET4 根因

在模型加载前失败：

```text
pydantic ValidationError: VllmConfig
draft_window_graph_numeric_diagnostic
Unexpected keyword argument
```

- 最先发生的是 producer/引擎配置错误；不是设备数值错误。
- `numeric-reference.json` 和 `controlled-target.json` 未生成；checker 的 `INVALID_EVIDENCE` 是缺失产物的下游结果。
- 位置：`tools/p7x_graph_repair2.py:1004` 设置 `additional_config.draft_window_graph_numeric_diagnostic`；pinned vLLM `VllmConfig` 在引擎配置构造时拒绝该键。
- 没有加载模型、没有 sample/chunk、没有数值证据。
- 换卡不能修复该配置契约错误；未在服务器修改源码重试。
- 详细：`reports/NUMERIC_TARGET4_FAILURE.json`。

## 6. 设备重分配细节

### 6.1 旧进程释放

- B2 旧设备进程树（host PIDs 871639/872251/872571/872893）：
  - TERM 到本任务子进程组 872893；
  - launcher `returncode=143`；
  - runner `EXECUTION_FAILED`；
  - **无残留本 campaign 进程**；
  - partial 与 campaign 保留。
- 最小只读 probe 已正常退出。
- NPU0–3 当前无本 campaign 进程；NPU4–7 仍有其他 PID，未终止/未 reset。

### 6.2 映射

`npu-smi info -m`：

```text
Chip Logic ID = Chip Phy-ID = 0..15
```

旧：`ASCEND_RT_VISIBLE_DEVICES=8` → NPU4/Chip0/Phy-ID8。
新尝试：`ASCEND_RT_VISIBLE_DEVICES=0` → torch `device_count=1/current=0`，实际仍 NPU4/Chip0/Phy-ID8。

结论：当前容器只暴露后段设备或以 offset 方式映射；需要容器设备重映射，不能仅改环境变量。

## 7. Profiling

- 本轮未执行新的 8 个 normal/control、detailed 或 PROFILE_LIFE。
- 原因：设备映射阻断；模型启动被停止。
- `Repair6_Profiling_Summary.json` 状态 `BLOCKED_DEVICE_MAPPING`。
- 旧 Repair5 trace 仅作为历史参考，不能作为 Repair6 当前 SHA/合法设备证据。
- 四个新 Host 子 range 的 installed/count/coverage 未验证；TASK_INTERNAL/PHYSICAL_READ 仍 OPEN。

## 8. LIFE 与 ABORT

因设备纠正，C2、LIFE、四个 ABORT 均未执行：

```text
BLOCKED_DEVICE_MAPPING
```

不得把旧 Repair5 的 LIFE/ABORT 结果当成当前 SHA 或合法设备结果；不得把进程退出当设备完成；不得解冻 public Graph。

## 9. G1–G5 映射

| Gate | 状态 | 说明 |
|---|---|---|
| G1 operator boundary | PASS_OLD_DEVICE_SEGMENT | B0 host operator boundary 21 gens |
| G1 task internal | OPEN | 无 operand 地址接口 |
| G2 A/B/A′ | BLOCKED | 无新设备；旧 B0 host rows 不能替代 |
| G3 canonical/oracle | PASS_OLD_DEVICE_SEGMENT | B0/B1 oracle；非 full physical |
| G3 physical read | OPEN | capability gap |
| G4 write/head | PASS_OLD_DEVICE_SEGMENT | B0/G4F/G4 natural 部分 |
| G4 full target Base | PARTIAL_PREFIX_VALID | 10 pairs PASS；Base `(4,32)` expected BLOCKED |
| G4 full target Target4 | SAMPLE_COMPLETE | 12/12 pairs zero tolerance；old segment；external join required |
| G5 lifecycle | OBSERVED_NORMAL_ORDER_NOT_REUSE_PROOF | 仅 NORMAL_ORDER；normal reuse/effective generation UNPROVEN |
| G5 private | BLOCKED | 无新设备 C2/LIFE |
| ABORT | BLOCKED | 未执行 |
| BASE_G1_G5_VERIFIED | NO | 多个 open/blocked |

## 10. 失败分类

### 已证实 production Window 数值缺陷

**无。** TARGET4 12/12 零容差 PASS 是强正向证据；G4F Base 的 `(4,32)` 是合同 expected OPEN，不是缺陷。

### 新配置契约问题

`NUMERIC_TARGET4` 的 `VllmConfig` unexpected keyword 是当前 SHA 的配置/集成契约问题；阻止了 capture sink 和连续数值验证。需要本地修复后重新发布，不能在服务器打补丁。

### 设备/环境阻断

当前容器不能选择 host Phy-ID0–7；这是 container mapping blocker，不是 production 数值失败。

### Fixture/inventory

Base target `(4,32)` absent 是 expected OPEN；Target4 独立 12 样本证明扩展 inventory 存在，但不能反向改写 Base。

### 平台/验收

task operand、physical read、UPDATE effective generation、completion owner、normal reuse 仍需要平台维护者/验收 owner 明确语义或替代证据。

## 11. 下一步

### 必须先做

1. 容器 owner 将 host Phy-ID0–7 正确映射到容器可见 device，重新核对 `npu-smi info -m` 和最小 allocation probe；不得再使用 Phy-ID8–15。
2. 本地修复 `additional_config.draft_window_graph_numeric_diagnostic` 到 pinned `VllmConfig` 的契约；不要在服务器修改。
3. 修复后新发布 SHA/tree，重新 P0/A0/A1/B0 锚点。

### 设备纠正后最小重测

- P0 + A0/A1/B0（新合法设备）；
- B2（上次被设备纠正中断）；
- C2、LIFE、ABORT 四点；
- O0/O1 与自然 long/mixed；
- 8 normal/control + necessary detailed + PROFILE_LIFE。

### 可复用

- 旧设备段 P0/A0/A1/B0、PREFIX、G4F 10/10、TARGET4 12/12、NORMAL_ORDER、B1 作为回归/诊断基线；
- 旧 Repair5 profiling 仅历史参考；
- 所有旧段结果标注 `old_die8`，不得作为新合法设备正式证据。

### 不能做

- 不使用 Phy-ID8–15；
- 不修改 production/checker/Graph 顺序/容差；
- 不复制旧 PASS 冒充新 attempt 依赖；
- 不把 TARGET4 结果扩成 Base 支持；
- 不把诊断结果升级为正式 Graph 支持；
- 不解冻 Public Graph。

## 12. 回传

报告、42-case 状态、plan、launcher/campaign/checker、Target chunk manifest、NUMERIC 失败、设备纠正记录和平台问题单进入 review；完整 tensor chunks/partial 进入 raw。回传包与 manifest 见 `Repair6_DOWNLOAD_MANIFEST.json`。

仅声明 `SERVER_PACKAGE_INTEGRITY=VERIFIED`；`RECEIVER_INTEGRITY=NOT_YET_VERIFIED`。包完整性不等于设备正确性。
