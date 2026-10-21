# P7-X MRV2 Draft Sliding Window — Node101 Ascend A3 Repair5 服务器最终报告

- RUN_ID：`20261020T144145Z_d0a3fc3d`
- RUN_ROOT：`/mnt/wenqing/mrv2_graph_repair5_verify/20261020T144145Z_d0a3fc3d`
- 最终源码：`d0a3fc3d42d7d97e5e7da3890d2710263a097e63`
- tree：`2f6b93415ced94fe3f4ba22c518699a023b97511`
- parent：`3bdc413aa9826e4c199f5d96125e71db2c343420`
- pinned vLLM：`84030bbe3d74d99bad477a3d2e37a973ccd8865c` / tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`
- 主机：`node-39-101`；logical die 8 → `npu:0`
- Python 3.11.10；torch 2.10.0+cpu；torch_npu 2.10.0.post4；CANN 9.1.0
- 公开 Graph Gate：`STILL_FROZEN`
- 最终动作：`RETURN_TO_LOCAL_CODE_FIX`

## 0. 最终状态摘要

```text
FINAL_SOURCE = d0a3fc3d42d7d97e5e7da3890d2710263a097e63 / 2f6b93415ced94fe3f4ba22c518699a023b97511
BASE_PROFILE = capture_sizes [7,14,28]; Draft (1,7)/(2,14)/(4,28); Target (1,8)/(2,16), no (4,32)
TARGET4_PROFILE = capture_sizes [7,14,28,32]; Target (1,8)/(2,16)/(4,32); Draft (1,7)/(2,14)/(4,28)
PLANNED_CASES = 35
EXECUTED_CASES = 35
P0 = PASS
A0/A1/B0 = PASS / PASS_EXPECTED_NEGATIVE / PASS
B1/B2/O0/O1 = PASS / PASS / PASS_FUNCTIONAL / PASS_FUNCTIONAL
C2 = PASS_SCOPED_PRIVATE_FIA (fixture PASS; production integration PARTIAL)
NATURAL_G4 = short PASS, long1 PASS, long2 FAIL (alignment-required), mixed FAIL (cardinality)
CONTROLLED_TARGET_BASE = BLOCKED (512 MiB checkpoint budget)
CONTROLLED_TARGET4_EXTENSION = BLOCKED (same budget; inventory (4,32) actually captured)
REAL_MRV2_TOKEN_ABA = FAIL / NOT_ASSESSED (controlled target child failed; no tokens A/B/A')
CONTINUOUS_NUMERIC_REFERENCE = NOT_IMPLEMENTED
LIFE_DIAGNOSTIC = PASS_DIAGNOSTIC_SERIALIZED
NORMAL_PATH_REUSE = OPEN
ABORT = 4/4 EXPECTED_QUARANTINE_OBSERVED (child rc=73, no timeout/signal)
PROFILING_COLLECTION = PASS (8 normal/control + PROFILE_LIFE actual traces)
PROFILING_ANALYSIS = PASS_SCOPED (fields/host stats; target-flow/physical/completion unresolved)
TASK_INTERNAL = OPEN
PHYSICAL_READ = OPEN
BASE_G1_G5_VERIFIED = NO
PUBLIC_GRAPH_GATE = STILL_FROZEN
SERVER_PACKAGE_INTEGRITY = VERIFIED (local package integrity; receiver not yet verified)
RECEIVER_INTEGRITY = NOT_YET_VERIFIED
NEXT_ACTION = RETURN_TO_LOCAL_CODE_FIX
```

本报告不把工具执行成功、请求完成、profiler 成功、checker exit 0 或 HEAD_ONLY 相等当作正式 Graph/G1–G5 通过。

## 1. 输入、发布与源码身份

### 1.1 输入核验

- `P7X_Graph_Base_A3_Repair5_Server_Input_Pack.zip`：bytes 35,287，SHA256 `1288673bca8ea9e58dcc01e8b7448ae5a1fad27eb96e4470333d5fa8d1106746`。
- `P7X_Graph_Base_A3_Repair5_Server_Handoff.json`：bytes 142,554，SHA256 `f4ff8891fe44d08e89c851c4a3c985902f338e5997ca07912d83515c127efc90`。
- handoff 文件内外的 bytes/SHA256 完全一致；input pack 21 个成员的 `SHA256SUMS` 全部通过。
- publication：`VERIFIED`；clean room：`VERIFIED`；`new_sha_device_verification` 在执行前为 `NOT_RUN`。
- 没有使用旧 `3bdc413a` PRE_PUBLICATION input pack 或 handoff。

### 1.2 独立 GitHub checkout

- repo：`https://github.com/LucianWQZ/vllm-ascend.git`
- 从 branch `fix/p7x-graph-base-a3-repair5` clone 后 detach 到 `d0a3fc3d...`。
- HEAD/tree/parent 精确匹配；parent `3bdc413a` 是祖先；Review4 baseline 也是祖先。
- ascend 与 vLLM 两仓 `git status --porcelain` 均为空。
- `VERIFY_SOURCES.py` 输出 `EXACT_SOURCE_ONLY`；其自身声明不包含 import、模型、发布或设备正确性。

### 1.3 工具哈希

全部匹配 handoff：

- `tools/p7x_graph_g1_g5.py` `8c29e83d396bb06eb718e67c65aeb2085a18efd182cbd311f2b7da9defb2f64c`
- `tools/p7x_graph_repair2.py` `f133561299617686df1b08dffaeb4e70140a73c37019f0c08a5b1091acc5a040`
- `tools/p7x_graph_repair4_acceptance.py` `6386ce1c2a21b249a0dd62e088a1c5a11e25c734500d03363d83db65bd5e8ead`
- `tools/p7x_graph_repair4_campaign.py` `7889b2f6eccbd9490770789d47575db19c4734598386c897e8f79c9fb491a3e6`
- `tools/p7x_graph_repair4_fixture.py` `4033947f76f36b6f224a4fc048a4d7aaff8e8ff0ac036c2d48bce3cd86a7baf6`
- `tools/p7x_graph_repair4_target.py` `0390337e1c33976835596ee910e9a1847d3615ef4870ec2195947712d266dc7f`
- `tools/p7x_graph_repair5.py` `d7fc7349a535135249c13fa7f6982c04c748d0ea8a6ac1d2481af38c78d06d12`
- `tools/p7x_graph_repair5_campaign.py` `9089f2baf0e2f3bb9757239405ca238e700494c74535cc0ca2f68439e5a87684`
- `tools/p7x_graph_repair5_evidence.py` `bade0d9c4a6a909de2ddddaea91c2cc10237f3c006d4520e02150cb361d120a9`
- `tools/p7x_graph_repair5_lifecycle.py` `e3ef43f76fb7d28dbfefee4b5609c1183b8c954bff894859ef37f13ec5a7fa6d`
- `tools/p7x_graph_repair5_pack.py` `66fa6f85b0f9fd37c3aecbecb26f6af288710099a0f61e43b8a39e43945e1bed`
- `tools/p7x_graph_repair5_profile.py` `7f57c39139f0551fc4fbd490df4ac05fb1110716e66dc3d3612f31b1001e699f`
- `tools/p7x_graph_repair5_target.py` `d8dc074f23729d9489f0681884ee9c94a9ef677bdbf0170a531b20822a3c8629`

### 1.4 fixture 与运行 provenance

- fixture manifest SHA256：`1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4`；10/10 文件匹配。
- overlay：618 个 `.py` 来自精确 d0a3fc3d，1269 个非 Python 文件来自本机已安装 A3 donor；donor Python 被排除。
- 实际导入：
  - `vllm` → `runtime/graph_char_overlay/vllm/__init__.py` → 精确 `src/vllm/vllm`
  - `vllm_ascend` → overlay 精确源码
  - `NPUModelRunner` → `vllm_ascend.worker.v2.model_runner`
  - `AscendDSparkSpeculator` → `vllm_ascend.worker.v2.spec_decode.dspark.speculator`
- sitecustomize 阻止了 `/home/wenqing/vllm-main`、`/home/wenqing/vllm-ascend-main` 及旧 MRV2/Repair 路径的 Python 导入。

证据：`artifacts/reports/SOURCE_IDENTITY.json`、`artifacts/reports/ENVIRONMENT_FACTS.json`、`runtime/build_overlay.sh`、`runtime/env_repair5.sh`、`runtime/site/sitecustomize.py`。

## 2. 环境、资源与冻结计划

- 启动时 die8 空闲 HBM 60.873 GiB；设备无其他进程；未 kill、未 reset、未抢卡。
- 开始时 `/mnt` 可用约 44G，结束时约 23G；raw 证据较大，打包采用分片/内容分包。
- `P0` capabilities：`EXECUTION_APIS_AVAILABLE`，`model_loaded=false`，`device_execution=NOT_RUN`，native semantics `UNPROVEN`。
- profiler preflight：`APIS_AVAILABLE_DEVICE_NOT_RUN`；`torch_npu.profiler.profile` version 2.10.0.post4。
- 35-case plan 由已提交 `tools/p7x_graph_repair5_campaign.py` 生成，非 example 占位路径；`artifacts/retry1/case-plan.json` SHA256 `0b7f1f01f1c88b3308b3c484841e8876ac6473d72925539f826fa3cbfc6ad2ff`。
- 初始 `artifacts/case-plan.json` 的 A0 失败是环境 `PYTHONPATH` 缺少 CANN `acl`；保留原失败 attempt，使用新的 `artifacts/retry1/` frozen plan 重试，A0 随后 PASS。

## 3. 35-case 实际执行矩阵

所有 35 个 case 均有 orchestration 记录；没有静默遗漏。逐项机器记录见 `artifacts/reports/Case_Status.json`、`Case_Status.csv`、`commands/Execution_Ledger.jsonl`。

| # | case | 结果 | 关键事实 |
|---:|---|---|---|
| 1 | P0 | PASS | capabilities API 可用；native semantics 未证明 |
| 2 | A0 | PASS（retry1） | Window OFF；1/2/4 × 16 tokens；joint PASS |
| 3 | A1 | PASS_EXPECTED_NEGATIVE | `GRAPH_FROZEN` NotImplementedError；不是资源失败 |
| 4 | B0 | PASS | 21 generations；3 replay buckets；105 update；21 retire；joint PASS |
| 5 | C2 | PASS_SCOPED_PRIVATE_FIA | fixture PASS；production integration PARTIAL；G5 diagnostic completion |
| 6 | B1 | PASS | 47 generations；75 rows；14 行 S>0；S=128/1024；official joint PASS |
| 7 | B2 | PASS | 14 generations；32 rows；10 行 S>0；3-active/4-padded 与 4-active/4-padded；official joint PASS |
| 8 | O0 | PASS_FUNCTIONAL | observer OFF；1/2/4 完成；joint PASS |
| 9 | O1 | PASS_FUNCTIONAL | observer OFF；11 组 16 tokens；joint PASS；snapshot 空 |
| 10–11 | G4_OFF/ON_short | PASS | 21/21；write/head 官方 PASS |
| 12–13 | G4_OFF/ON_long1 | PASS | 12/12；write/head 官方 PASS |
| 14–15 | G4_OFF/ON_long2 | SINGLE_ARM_STRUCTURE_VALID | 两臂完成，但官方 compare FAIL（alignment） |
| 16–17 | G4_OFF/ON_mixed | SINGLE_ARM_STRUCTURE_VALID | 两臂完成，但 18 vs 14 官方 cardinality FAIL |
| 18–21 | G4F_OFF/ON、TARGET4_OFF/ON | BLOCKED | 512 MiB checkpoint 预算在 forward 前阻断，无 CAPTURED |
| 22 | LIFE | PASS_DIAGNOSTIC_SERIALIZED | 21 generations；结构化 recorder 关联 |
| 23–26 | ABORT_before/after_replay/after_update/after_completion | EXPECTED_QUARANTINE_OBSERVED | child rc=73；无 timeout/signal；quarantine |
| 27–34 | PROFILE_OFF/ON_short/long_control/normal | PASS_SCOPED_PROFILING | 8 个 active replay + trace；control 无 native profiler |
| 35 | PROFILE_LIFE | PASS_SCOPED_PROFILING | DIAGNOSTIC_SERIALIZED；28 generations |

## 4. B0 / B1 / B2 / O0 / O1

### 4.1 B0

- 21 generations；snapshot 132 events、120 operand_events、21 G4、147 lifecycle。
- lifecycle：21 `replay_submitted`、105 `update_event_recorded`、21 `proposal_retired`。
- replay buckets：`(1,7)=7`、`(2,14)=7`、`(4,28)=7`；missing 为空。
- 输出：1/2/4 请求批次，每个请求 16 tokens。
- None-return 合同：21 条 generation 全部 `draft_output_status=OUTPUT_NOT_CAPTURED`、`draft_output_reason=GRAPH_MANAGER_RETURNS_NONE`；没有伪造 hash；没有恢复 `ExternalEvent.query`。
- 官方：`EVIDENCE_INTEGRITY=PASS`、`HOST_CONTRACTS=PASS`、`B0=PASS`、joint PASS；但 task/physical/completion 仍 OPEN。

### 4.2 B1 长窗口

- 47 generations；288 events、250 operand_events、47 G4、329 lifecycle。
- 75 runtime oracle 行；14 行 S>0；S 实际为 128 或 1024。
- descriptor 行分布：`(1,7)=33`、`(2,14)=14`、`(4,28)=28`。
- E 覆盖 12…2075；runtime E=32/1024/1025/1151/1152/1153/2049 均未到达；`S=0`、`S>0`、`non_block_end` 由 host/oracle 覆盖。
- 官方 joint PASS；所有 10 组请求 16 tokens 完成。
- 没有 generation-associated 连续数值输出，不能把 16 tokens 当长窗口数值正确。

### 4.3 B2 混合

- 14 generations；90 events、85 operand_events、14 G4、98 lifecycle。
- 4 组混合请求全部 16 tokens；32 runtime 行，10 行 S>0（S=1024）。
- 实际 padded bucket：
  - generation 4/5/6：descriptor `reqs=4;tokens=28`，3 个 active 请求，`valid_counts=[1,9,17]`；
  - generation 7/8/9：同 descriptor，4 个 active 请求，`valid_counts=[1,2,9,17]`。
- 这是实际 snapshot/oracle 记录，不是从请求数推断。
- 官方 joint PASS。

### 4.4 O0/O1

- O0：provider true，observer false；1/2/4 完成。
- O1：provider true，observer false；11 组 16 tokens；snapshot 空（observer 关闭，符合预期）。
- 仅功能对照，不关闭数值/物理 Gate。

## 5. C2 私有 FIA

`C2/result.json` 状态 `COMPLETE`；`C2/check.json`：

```text
fixture=PASS
production_integration=PARTIAL
G5=PASS_DIAGNOSTIC_LAST_CONSUMER_COMPLETION
ready=false
```

数值关系（直接由落盘 output 重算）：

| 对比 | 结果 | max_abs |
|---|---|---|
| A vs A_prime | 完全逐位相等 | 0.0 |
| A vs B | 可区分 | 15.0078125 |
| A vs outside_only | 完全逐位相等 | 0.0 |
| A vs inside_only | 可区分 | 0.25 |
| A vs A_restore | 完全逐位相等 | 0.0 |

- A/B 均为 1024 长度，A_prime 恢复 A；outside_only 只改窗外 V，结果与 A 相等；inside_only 改窗内 V，结果变化；A_restore 恢复。
- 每个 record 有 canonical table、full table、binding、completion event、generation/epoch；`completion.verified=true`。
- 容差预声明 atol=0.016/rtol=0；fixture checker PASS。
- **production_integration 仍 PARTIAL**：capture inputs 未走 DFlash 真实 helper/model runner，production write 未执行；C2 不替代完整 MRV2。
- G4F 仍 `BLOCKED`：私有 fixture 没有 target model/head/logits；C2 的 G5 仅 diagnostic last-consumer completion。

## 6. 自然 G4

| 组 | 基数 | 官方 write | 官方 head | 独立审计 |
|---|---:|---|---|---|
| short | 21/21 | PASS | PASS | 21/21 visible、physical、head 全相等 |
| long1 | 12/12 | PASS | PASS | 12/12 全相等 |
| long2 | 14/14 | FAIL | FAIL | 6/14 visible、3/14 physical、11 position mismatch；4/14 输入对齐且全部逐位相等；10/14 不对齐 |
| mixed | 18/14 | FAIL | FAIL | cardinality 不等，无法配对 |

- long2 官方 errors：`sample 1 after semantic mismatch`、`hidden_states differs at 1`。
- mixed 官方 errors：`full_write_target sample cardinality differs`、`target_logits_head sample cardinality differs`。
- long2 的 4 个对齐样本：hidden_states/logits 逐位相等，max_abs=0.0；因此不能把这 4 个样本外推为整组 FAIL，也不能把整组判为生产数值错误。
- 官方 FAIL 原样保留；HEAD_ONLY 与 FULL_TARGET 分开，`full_target_numeric` 全部 OPEN。

## 7. 受控完整 Target Base / Target4

四臂均实际到达 `STARTUP_COMPLETE`，随后在 `p7x_graph_repair4_target.py:341` 的 `reserve < budget[0]` 检查处失败：

```text
EvidenceError: budget cannot hold post-forward KV and output
```

- `DEFAULT_MAX_BYTES=512 MiB`；实际单个 `controlled-target.pt` 约 5.31 GB。
- G4F_OFF/ON、TARGET4_OFF/ON 四臂均无 CAPTURED 样本；target-joint 和 aba-joint 均 FAIL。
- Base target inventory：`(1,8)`、`(2,16)`，没有 `(4,32)`（符合 Base 合同，expected OPEN）。
- Target4 inventory：`(1,8)`、`(2,16)`、`(4,32)`，Draft `(1,7)`、`(2,14)`、`(4,28)`；扩展 descriptor 确实被捕获。
- `compare-target` 对 G4F_ON/TARGET4_ON 在编排层 300s 超时（`ORCHESTRATOR_TIMEOUT`），没有 paired 输出；这不是数值结果。
- 该失败是工具/预算契约缺陷，不是 native 异常，也不是 production 缺陷；`G4F` 的 layer inventory 检查本身已不再报错。

## 8. 真实 MRV2 token ABA 与连续数值

- `REAL_MRV2_TOKEN_ABA`：`check-diagnostic --kind aba` 在 G4F_ON/TARGET4_ON 均因受控 target child 失败而 FAIL；没有 A/B/A' token 记录。
- `REAL_MRV2_CONTINUOUS_NUMERIC_REFERENCE=NOT_IMPLEMENTED`：批准源码/handoff 明确没有连续 hidden/logit Window reference；未在服务器临时补 hook。
- B1/B2 的 token-level oracle 与 C2 私有 FIA 均不能替代连续数值参考。

## 9. 生命周期与 Abort

LIFE：

- `PASS_DIAGNOSTIC_SERIALIZED`；21 generations；recorder/launcher/campaign/plan 关联通过。
- `diagnostic.status=STRUCTURE_VALID_NOT_EXECUTION_ACCEPTED`；`normal_overlap=UNPROVEN`；`update_effective_generation=UNPROVEN`。
- 仅诊断串行化路径，不是正常无额外同步的 backing 复用安全。

四个 ABORT：

- child returncode 73，`timeout=false`，无 signal；官方 joint 均 `EXPECTED_QUARANTINE_OBSERVED`。
- `device_completion=UNPROVEN`，`reuse=FORBIDDEN`；没有把进程退出当设备完成。
- 失败点分别 before_replay / after_replay / after_update / after_completion。
- 未发生意外 exit74/超时/信号；没有在原进程继续服务或复用 backing。

## 10. Profiling

- 8 个正常/控制 case + PROFILE_LIFE 全部实际采集；所有 normal 有 active Graph replay：
  - short：21 次 Draft replay；
  - long：47 次 Draft replay。
- descriptor：
  - short：`(1,7)=7`、`(2,14)=7`、`(4,28)=7`；
  - long：`(1,7)=33`、`(2,14)=7`、`(4,28)=7`；
  - Base Target：`(1,8)=6`、`(2,16)=6`；没有 `(4,32)`。
- ON long 的 immutable Window descriptor 实际有 14 个 active `source_start_column>0`（值 1 或 8）。
- 实测 trace：
  - short normal：约 10,893 kernel 行、53,459 operator 行、20,052 task 行；
  - long normal：约 24,640 kernel 行、108,439 operator 行、46,584 task 行；
  - 存在 `acl_memcpy_host_to_device` 1221、`acl_memcpy_device_to_host` 141（long ON normal），但没有 bytes 字段；
  - `Event::synchronize`、enqueue/dequeue、async flow 事件存在。
- `kernel_details.csv` 的 `Type` 全为 `N/A`；`Input Shapes`/`Call Stack` 为空；没有 operand 地址/物理读集/完成 owner。
- Host submission 统计（`Draft_REPLAY_PLUS_UPDATE` mean）：
  - OFF short control 1.337 ms → normal 1.555 ms（+16.3%）
  - OFF long control 1.228 → 1.649（+34.3%）
  - ON short control 2.578 → 2.942（+14.1%）
  - ON long control 2.662 → 2.885（+8.4%）
  - 这些只是诊断性对照，不是 release 加速结论。
- PROFILE_LIFE：Draft_REPLAY_PLUS_UPDATE mean 约 1062 ms，明确串行化，单独说明，不参与正常性能比较。
- `TASK_INTERNAL`、`PHYSICAL_READ`、`UPDATE effective generation`、`completion` 仍 OPEN。

详细分析：`artifacts/reports/Repair5_Profiling_Report.md`、`Repair5_Profiling_Summary.json`。

## 11. G1–G5 分层映射

| Gate | 本轮证据 | 实际证明范围 | 缺口 | 下一步 |
|---|---|---|---|---|
| G1 operator boundary | B0 15 capture/105 update，host contract PASS | host operator boundary | task-internal operand 地址 | 定义/实现 operand trace |
| G1 task internal | profiling 有 host range/task/stream，无 operand | 不足以证明 task operand | capability/验收字段 | CANN/torch_npu 支持或验收决定 |
| G2 A/B/A′ | B1/B2 全序列 scan complete，无 device candidate | 无 ABA candidate | 设备 refresh/受控多代重用 | 设计 G2 fixture |
| G3 canonical/oracle | B0/B1/B2 oracle rows，B2 padded descriptor | host/device effective inputs | 物理读集 | 物理事务字段或验收决定 |
| G4 write/head | short 21/21、long1 12/12 PASS | write + HEAD_ONLY | FULL_TARGET | 修 Target 预算后重跑 |
| G4 full target | 四臂 budget BLOCKED | 无 CAPTURED | checkpoint budget | R5-F01 |
| G5 lifecycle | LIFE 21 gens, recorder join | 诊断串行化 | normal overlap/effective generation | 诊断语义/接口 |
| G5 completion | C2 checkpoint last-consumer verified | 私有 fixture completion | 正常路径 completion owner | 平台能力/验收 |
| G5 private | C2 fixture PASS | 私有 FIA 数值 | production integration PARTIAL | 后续接入 |
| ABORT | 4/4 rc73 quarantine | 受控隔离 | 设备完成/安全复用 | 已满足本轮诊断目标 |

## 12. 失败分类

### 已证实 production 缺陷

**无。** 本轮没有对齐且可复现的 production Window 数值错误，也没有 production 调度/allocator/replay/UPDATE 顺序证据。

### 工具/观测器缺陷

1. **R5-F01**：受控 Target checkpoint 的 512 MiB 预算小于完整 Target KV+output（约 5.31 GB）；`p7x_graph_repair4_target.py:52/:341`，`p7x_graph_repair5_target.py:146`。
2. **R5-F02**：`RUN_CASE.py:36` 对 `compare-target` 的 300s 限制在大 artifact 上超时；G4F_ON/TARGET4_ON 无 paired 输出。

### fixture/coverage 不足

3. **R5-F03**：自然 G4 long2/mixed 仍按索引配对，缺少确定性 request/phase/slot/position；long2 4/14 对齐、10/14 不对齐；mixed 18 vs 14。
4. **R5-F04**：真实 MRV2 连续 hidden/logit Window reference 未实现（`NOT_IMPLEMENTED`）。
5. **R5-F05**：task-internal operand、physical read-set、completion owner 无可用字段。

### 环境

- 初始 A0 的 `acl` 缺失是 campaign `PYTHONPATH` 编排错误，已用新 plan 修复并保留旧失败；不是设备环境 blocker。
- 设备全程健康；没有 kill/reset/抢卡。

### 验收决策

6. **R5-F06**：G4 完成是否要求 FULL_TARGET，还是接受 HEAD_ONLY+write。
7. **R5-F07**：Base `(4,32)` 缺失是合同 expected OPEN；Target4 只作为独立诊断，不得扩展为 Base/产品支持。

## 13. Gate 状态

完整机器记录：`artifacts/reports/GATE_DECISIONS.json`、`GATE_STATUS.csv`。

| Gate | 状态 |
|---|---|
| PACKAGE_INTEGRITY | PASS（本地打包后验证） |
| SOURCE_IMPORT_FIXTURE | PASS |
| REQUEST_EXECUTION | PASS |
| OPERATOR_BOUNDARY | PASS |
| PRIVATE_FIA_NUMERIC | PASS（fixture；production integration PARTIAL） |
| NATURAL_G4_WRITE_HEAD | OPEN（short/long1 PASS；long2/mixed alignment） |
| CONTROLLED_TARGET_BASE | BLOCKED |
| CONTROLLED_TARGET4_EXTENSION | BLOCKED |
| REAL_MRV2_TOKEN_ABA | FAIL/NOT_ASSESSED |
| REAL_MRV2_CONTINUOUS_NUMERIC_REFERENCE | NOT_IMPLEMENTED |
| DIAGNOSTIC_COMPLETION | PASS_DIAGNOSTIC_SERIALIZED |
| NORMAL_PATH_REUSE | OPEN |
| ABORT_QUARANTINE | PASS |
| TASK_INTERNAL | OPEN |
| PHYSICAL_READ | OPEN |
| PROFILING_COLLECTION | PASS |
| PROFILING_ANALYSIS | PASS_SCOPED |
| BASE_G1_G5 | OPEN / NO |
| PUBLIC_GRAPH_GATE | STILL_FROZEN |

## 14. 回传

- `Repair5_review.zip`：报告、机器记录、35-case 账本、冻结 plan/requests、launcher/campaign/checker、关键原始样本、profiling 摘要。
- `Repair5_raw.zip` 或内容分包/分片：全部 tensor/checkpoint、target-boundary、profiler 原始目录与 CSV/DB、stdout/stderr、partial、失败 attempt。
- `Repair5_DOWNLOAD_MANIFEST.json`：run/source/profile/config 身份，包/分片 bytes/SHA256/顺序，成员索引，在线评审集与本地完整复核集。
- `Repair5_RECEIVER_VERIFY.py`：流式顶层/分片/重组/ZIP CRC/成员/JSON 校验。
- `Repair5_Profiling_Report.md`、`Repair5_Profiling_Summary.json`。
- `NEXT_LOCAL_CODEX_INPUT.json`：finding_id、分类、严重性、源码位置、最小复现、证据路径、建议动作、依赖、最小重测矩阵、剩余不确定性。

仅声明 `SERVER_PACKAGE_INTEGRITY=VERIFIED`；`RECEIVER_INTEGRITY=NOT_YET_VERIFIED`。包完整性不等于设备正确性。

## 15. 结论与下一步

### 本轮实际确认了什么

- 精确 d0a3fc3d 源码/工具/fixture/overlay 身份成立。
- B0 真实设备路径通过；None-return 合同没有伪造 hash。
- B1/B2/O0/O1 正常请求与 observer-off 完整；token-ID prompt 的官方 joint 已 PASS。
- C2 私有 FIA fixture 数值 PASS；A/B 可区分、A′/restore 一致、窗外扰动不改变结果、窗内扰动改变结果；G5 diagnostic completion PASS。
- 自然 G4 short/long1 write/head PASS。
- LIFE 诊断串行化 PASS；四个 ABORT 预期隔离 4/4 PASS。
- 8 个 normal/control + PROFILE_LIFE 实际 trace 取得；long ON 有 14 个 `source_start_column>0` active descriptor。

### 是否存在已证实 production 缺陷

没有。当前阻塞是工具预算/超时、G4 配对、连续数值参考和平台观测能力，不是已证实的 production Window 缺陷。

### 哪些是工具/环境问题

- Target checkpoint 512 MiB 预算 vs 5.31 GB 数据（R5-F01）。
- compare-target 300s 编排超时（R5-F02）。
- 初始 A0 的 `acl` PYTHONPATH 编排错误（已修复，保留失败 attempt）。
- G4 配对/连续参考/平台字段不足属于 fixture/验收/平台，不应统一归为 production bug。

### 哪些结果可支持下一轮

- B0/B1/B2/O0/O1/C2/LIFE/ABORT 与 short/long1 G4 的 production 内容可作为 d0a3fc3d 的回归基线。
- 8 个 profiling 的字段/计数/host 统计可作为下一轮对照基线。
- 由于本地修复会产生新 SHA，这些结果不是新 SHA 的正式设备证据；新 SHA 仍需至少重跑 P0、锚点与受影响 case。

### 下一轮最小代码改动与重测

1. 修复 `p7x_graph_repair4_target.py` 的 checkpoint 预算/分块（R5-F01），保留完整 KV/输出声明与 16 GiB 总预算。
2. 修复 compare-target 的大 artifact 读取/超时（R5-F02）。
3. 增加 G4 long2/mixed 确定性配对和 logical remap（R5-F03）。
4. 重测：P0、G4F_OFF/ON、TARGET4_OFF/ON、官方 target/aba/compare-target；全量新 SHA 收尾则重跑 35 case。
5. 不修改 production/pinned vLLM；不通过减少样本、截断 KV、放宽容差或删除 FAIL 来“修复”。

### 哪些缺口需要维护者/验收 owner

- G4 是否要求 FULL_TARGET（R5-F06）。
- task-internal operand、physical read-set、completion owner 的平台字段/语义（R5-F05）。
- 真实 MRV2 连续数值参考是否必须实现（R5-F04）。
- Base `(4,32)` 缺失与 Target4 独立范围的验收边界（R5-F07）。

public Graph Gate 保持 `STILL_FROZEN`。本轮不继续性能、不运行 Batch A、不声称 receiver 验证，也不 push/修改代码。
