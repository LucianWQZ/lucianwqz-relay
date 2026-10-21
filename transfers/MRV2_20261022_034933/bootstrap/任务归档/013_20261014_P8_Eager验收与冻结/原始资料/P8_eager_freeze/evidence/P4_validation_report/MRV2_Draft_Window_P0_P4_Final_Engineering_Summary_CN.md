# MRV2 Draft Sliding Window：P0–P4 最终工程总结

> 生成日期：2026-10-13（Asia/Shanghai）  
> 文档性质：P0–P4 唯一工程入口；后续 P5–P8 必须从本文记录的源码、证据边界和 Gate 状态继续。  
> Production 代码：本轮未修改。  
> Release 状态：**HOLD**。

## 1. 一页结论

MRV2 `draft_window_size` 已完成从 policy、整数数学、canonical FullSource、runtime ownership，
到 Ascend-only eager Draft Attention consumer 的完整生产代码链。最终 production 只修改
`vllm-ascend`；vLLM 保持未经修改的固定基线。

当前可以准确声称：

- P1–P3 的代码和 CPU/static contract 已通过；
- P4a DFlash / eligible DSpark 的 Ascend-only eager 路径已实现并静态验证，但**没有 Window ON NPU 运行证据**；
- P4b Eagle3 static-K 的静态 contract 已通过；在 Node133 / Ascend 910B2（A2）、TP1、eager、
  `K=3, W=64` 的**单请求**精确路由上，已有 L3 状态证据和 L4 FIA operator 参数证据；
- 该证据不是 Level 5 kernel physical read-set，也不是多请求、Graph、Async、parallel 或性能证明；
- general online mixed arrivals 当前会触发 `NotImplementedError -> EngineDeadError`，两个请求失败且服务停止；
- 因此 `G-GQA-EAGER` 和 `G-AR-STEP` 均仍为 OPEN，P0–P4 required delivery 为 PARTIAL，
  Feature release 必须保持 HOLD。

最终裁决：

```text
P0–P3 PRODUCTION: PARTIAL
P4a STATIC: PASS
P4a NPU: OPEN
P4b STATIC: PASS
P4b SINGLE-REQUEST NPU: PASS
P4b MULTI-REQUEST NPU: OPEN
P0–P4 REQUIRED DELIVERY: PARTIAL
P5 DESIGN ENTRY: READY
P5 PRODUCTION GRAPH ENABLE: BLOCKED
FEATURE RELEASE: HOLD
```

`P0–P3 PRODUCTION: PARTIAL` 不表示 P1–P3 实现失败：P1、P2、P3 各自均为 Final PASS；
它反映服务器终局审计中 P0 owner acceptance manifest 仅有 frozen 文档、未在该轮 live re-derive，
且 P3 的真实 NPU completion/lifetime 仍未独立证明。

## 2. 权威输入与实际路径

本次读取的是以下实际文件；没有使用文件名后缀替代件：

| 类别 | 实际路径 |
|---|---|
| Frozen Design | `/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design.md` |
| Implementation Plan | `/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Draft_Window_Implementation_Plan.md` |
| P1 Notes | `/Users/wenqingzhang/Desktop/Note/MRV2/P1_Policy_Math_Types_Implementation_Notes.md` |
| P2 Notes | `/Users/wenqingzhang/Desktop/Note/MRV2/P2_Inventory_FullSource_Provider_Implementation_Notes.md` |
| P3 Notes | `/Users/wenqingzhang/Desktop/Note/MRV2/P3_Lease_Workspace_Transport_Store_Implementation_Notes.md` |
| P4a Notes | `/Users/wenqingzhang/Desktop/Note/MRV2/P4a_Ascend_Only_Eager_Integration_Implementation_Notes.md` |
| P4b Notes | `/Users/wenqingzhang/Desktop/Note/MRV2/P4b_Eagle3_StaticK_Eager_Integration_Implementation_Notes.md` |
| Freeze Snapshot | `/Users/wenqingzhang/Desktop/Note/MRV2/P4_freeze/MRV2_P0_P4b_Implementation_Snapshot.md` |
| Freeze Commit Manifest | `/Users/wenqingzhang/Desktop/Note/MRV2/P4_freeze/MRV2_P0_P4b_Commit_Manifest.md` |
| Freeze Full Diff | `/Users/wenqingzhang/Desktop/Note/MRV2/P4_freeze/MRV2_P0_P4b_Full_Diff.patch` |
| Server final report | `/Users/wenqingzhang/Desktop/Note/MRV2/Server_Final_Evidence/MRV2_Draft_Window_P0_P4_Server_Final_Evidence_Report_CN.md` |
| Server gates | `/Users/wenqingzhang/Desktop/Note/MRV2/Server_Final_Evidence/P0_P4_Server_Gate_Status.csv` |
| Server support matrix | `/Users/wenqingzhang/Desktop/Note/MRV2/Server_Final_Evidence/P0_P4_Server_Support_Matrix.json` |
| Server evidence index | `/Users/wenqingzhang/Desktop/Note/MRV2/Server_Final_Evidence/P0_P4_Server_Evidence_Index.md` |
| Conflict resolutions | `/Users/wenqingzhang/Desktop/Note/MRV2/Server_Final_Evidence/P0_P4_Server_Conflict_Resolution.csv` |

事实冲突时使用：生产源码/Git > 原始 trace/log 索引 > 服务器终局报告 > Implementation Notes >
Frozen Design > 推断。

## 3. 最终 Git 基线审计

### 3.1 vLLM

| 项目 | 事实 |
|---|---|
| repo | `/Users/wenqingzhang/Desktop/vllm/vllm` |
| HEAD | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |
| status | clean；`git status --porcelain` 为空 |
| private prototype | production 中不存在 `DraftAttentionReadInputs` 等 P4 prototype API |
| production/test diff | 无 |

### 3.2 vLLM-Ascend

| 项目 | 事实 |
|---|---|
| repo | `/Users/wenqingzhang/Desktop/vllm/vllm-ascend` |
| branch | `feature/p4b-eagle3-static-k` |
| upstream base | `841dc6ccdb134eab7ad09008859834d0572ee83f` |
| HEAD | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` |
| tree | `7d165d585755766e7493e02f0281598e4aca3602` |
| status | clean；`git status --porcelain` 为空 |
| base→final | 18 files，`+9706/-10` |

服务器使用的 observational debug SHA 为
`2a4856134648c068cab044ddfb11eb0e0d907453`。服务器审计核对了 6 个 debug commits，
均不是 production Final 的 ancestor；它们不得进入 production lineage。

## 4. 为什么从 MRV1 迁移到 MRV2

MRV1 的实现方式不能直接等价移植到 MRV2：MRV2 的 metadata、block table、speculator factory、
backend builder 和 speculative method 生命周期不同。安全迁移的核心不是“截短一个 tensor”，而是：

1. 在不改 scheduler/KV allocation 的前提下，建立 Draft-only read view；
2. 保持 canonical full block table、physical KV write、slot mapping、positions、query layout 和 Target 世界不变；
3. 明确 source owner、generation freshness、workspace 地址、reader completion 和 metadata owner；
4. 对不同 method 的 query width 与时序分别接入，而不是修改共享主流程；
5. unsupported route 必须在创建 inventory/workspace 前 fail closed，避免“部分支持”污染其它能力。

因此最终实现遵循“主流程不重写、在受控 extension point 增量接入”的原则。由于产品仓库边界
`R-REPO-01`，最终 seam 是 vllm-ascend 内部、instance-scoped、显式 typed transport 的有限
vendor-local metadata assembly；它避免 module global、ContextVar、shared owner swap，也避免修改 vLLM。

## 5. Frozen 核心不变量

以下是 P0–P4 不能因后续 P5–P8 改写的边界：

1. Window 只改变 **Draft Attention read visibility**。
2. Scheduler、physical KV allocation 和 canonical FullSource 不变。
3. `slot_mapping` 始终由 full canonical table 计算；Window 不参与 KV write address。
4. absolute positions、query layout、`query_start_loc` 与 Window OFF 等价。
5. Target metadata、Target read length、Target owner/content 不被 Draft Window 修改或 alias。
6. CONFIG_OFF 精确走 baseline；MTP 与 DeepSeek-V4 co-trained DSpark forced OFF，零 P2/P3/P4 state。
7. capability eligibility 不等于 runtime enablement；每个 backend/method/topology 单独关闭 Gate。
8. Window 总是从 canonical FullSource materialize，绝不 window-of-window。
9. mapping pointer/object identity 不是 freshness；`mapping_epoch` 必须 caller-owned、严格单调并全链路验证。
10. generation、request fingerprint、lane、phase/step、provider/source identity 必须一致；stale/ABA fail closed。
11. reader 未完成时 workspace 不得复用；exception/reset 也必须有唯一 retirement owner。
12. DraftMetadataStore 独立于 `model_state.attn_metadata`，包括 nested Tensor/NumPy storage。
13. vLLM 精确固定在 `84030bbe...`，production 只修改 vllm-ascend。
14. Graph、Async、prefix、parallel、complex backend 不能由 eager 单请求证据隐式打开。

## 6. 真实 delivery commit graph

```text
841dc6cc  vllm-ascend upstream feature base
  └─ b12399ad  P1 policy / math / types
      └─ c58daea0  P1 review-fix
          └─ 83579675  P2 inventory / FullSource / provider
              └─ fac84121  P2 review-fix
                  └─ feab28f5  P3 runtime ownership
                      └─ 16727882  P3 review-fix
                          └─ 0dd83e9f  P4a Ascend-only eager integration
                              └─ 4c1f6914  P4a review-fix
                                  └─ d0c88838  P4b Eagle3 static-K integration
                                      └─ 1011e2c2  P4b review-fix / Final
```

完整 per-commit 文件、parent、行数和依赖见
`P0_P4_Final_Commit_Manifest.md`；逐文件/函数映射见
`MRV2_Draft_Window_P0_P4_Code_Map.csv`。

## 7. 从配置到 NPU operator 的真实执行链

### 7.1 可变的 Draft read path

```text
draft_window_size
  ↓
init_speculator() / resolve_draft_window_policy()
  ↓
CONFIG_OFF ───────────────→ exact baseline
FORCED_OFF ─warning once─→ baseline + zero Window state
ELIGIBLE_ON
  ↓
DraftWindowRuntimeContext + capability inventory
  ↓
FullDraftKVSource (borrowed canonical full owner)
  ↓
P1 WindowPlan / P2 ReadDescriptor
  ↓
production mapping_epoch + ordered request fingerprint
  ↓
DraftWindowGenerationIdentity
  ↓
lease → stable workspace → materialize from FullSource
  ↓
immutable DraftMetadataInputs
  ↓ validate_for(expected identity)  [唯一正式消费边界]
  ↓
DraftMetadataStore (Draft-only; Target used only for alias audit)
  ↓
P4a DFlash/eligible DSpark one-proposal eager
        或
P4b Eagle3 first-pass + per-step frozen-anchor eager
  ↓
Ascend vendor-local metadata builder kwargs
  ↓
AscendAttentionMetadata / FIA operator arguments
  ↓
Draft Attention backend/operator
```

### 7.2 始终不变的 full/write/Target path

```text
Scheduler / KV allocation
  ↓
canonical full block table
  ├─→ full absolute positions / query layout
  ├─→ full slot_mapping ─→ physical KV write
  └─→ Target metadata / Target Attention / Target logits
```

两条路径的边界是本 Feature 最重要的工程事实：Window 是 Draft read view，不能成为新的 KV owner。

## 8. Phase-by-phase 最终工程解释

### 8.1 P0：设计与 Gate 冻结

P0 没有生产代码 commit。它定义 source priority、read/write 分离、Window 数学、phase boundary、
method/backend Gate、Graph/Async 后续路径和验证等级。服务器本轮没有 live re-derive owner manifest，
因此 P0 server gate 是 PARTIAL，而不是把 Design 判成错误。

### 8.2 P1：Policy、纯数学与类型

Commits：`b12399ad` + `c58daea0`。

- `spec_decode/__init__.py` 在保持 baseline factory 分支语义的同时，先做 CONFIG_OFF/FORCED_OFF/ELIGIBLE_ON。
- `draft_window.py` 建立 policy types、Window scalar plan、legacy-aligned anchor 与 capacity 数学。
- DFlash、DSpark、AR receiver 只接收 eligibility；P1 不创建 source/workspace，不接 Attention。
- forced-OFF 早于 numeric validation、inventory 和 workspace；unknown forced reason fail closed。
- review-fix 修正 identity normalization、warning scope、non-default geometry、factory parity 与 DFlash2 测试语义。

数据来源：用户配置与 method/model identity。Owner：speculator instance。Consumer：P2 capability builder。
OFF：直接 baseline。Unsupported：forced-OFF 或后续 Gate，不伪装 enable。

### 8.3 P2：Inventory、canonical FullSource、valid counts 与 provider

Commits：`83579675` + `fac84121`。

- 枚举真实 executable group 与 backend/layout，当前只批准 single-group dense-GQA direct-prefix candidate。
- `FullDraftKVSource` 借用 canonical full block table 与 count owner，不复制、不修改。
- valid counts 通过同一 `idx_mapping` 从 persistent request row gather 到 batch row；block id 0 是合法值。
- provider 计算 canonical `S` 和 direct-prefix source columns；source shortage/geometry mismatch hard fail。
- review-fix 补 FlashComm env Gate、int64 mapping、真实 BlockTables contract、独立 configured K 和
  pointer freshness 的 one-batch 限定，并把 `mapping_epoch` 冻结为 P3 mandatory requirement。

P2 结束仍没有 Window backing、lease、store 或 Attention consumer。

### 8.4 P3：Workspace、Lease、Typed Transport 与 Draft Store

Commits：`feab28f5` + `16727882`。

- `DraftWindowGenerationIdentity` 绑定 generation id、mapping_epoch、ordered request fingerprint、
  method/gid/provider/source/lane/phase/step。
- fixed-capacity `DraftWindowWorkspace` 拥有 Window table、valid counts、device/CPU exact、CPU upper；
  active rows/tail/padding 每代确定性写入，且与 canonical source 不 alias。
- lease pool 防止 active reader 覆盖；completion token、wrong retire、double retire、exception/ABA 都有状态机。
- immutable `DraftMetadataInputs` 是唯一 typed transport；不包含 positions、slot mapping 或 Target state。
- `DraftMetadataStore` 是 speculator-owned Draft store，publish 必须携带真实非空 Target metadata做完整 alias audit。
- review-fix 使 Target 参数 mandatory，扩展 MRO slots alias traversal，并补 empty/error retry tests。

P3 结束时 Attention 仍读 full；fake completion token 只证明 CPU state machine，不证明 NPU Async。

### 8.5 P4a：DFlash / eligible DSpark Ascend-only eager consumer

Commits：`0dd83e9f` + `4c1f6914`；其后 P4b review-fix `1011e2c2` 还更新了共享 pure-prefill classifier。

- `DraftWindowEagerMixin` 建立 production epoch provenance、一次 controlled host snapshot、P1/P2/P3 materialize、
  single validation boundary、Draft-private metadata build、publish/forward/retire。
- DFlash 使用真实 query width `K+1`；eligible DSpark 默认 `sample_from_anchor=True → K`，显式 false → `K+1`。
- Window OFF、dummy/profile、pure scheduler-prefill 都走 baseline full；mixed prefill/decode 在 Window state前拒绝。
- Window ON 只替换 Draft read table 和 read lengths；slot mapping仍来自 full `BlockTables.slot_mappings`。
- `attn_utils.py` 的 optional `seq_lens_cpu` seam 默认 None 保持 baseline；Window ON传 explicit CPU exact。
- Ascend-only seam 是硬约束下的有限 vendor-local assembly，并由 differential parity 与 upstream AST/signature
  drift guard保护；没有 vLLM dependency、global transport、ContextVar 或 owner swap。

P4a 没有 NPU Window ON证据，所以 `G-GQA-EAGER` 仍 OPEN。

### 8.6 P4b：Eagle3 static-K first-pass 与 AR per-step consumer

Commits：`d0c88838` + `1011e2c2`。

- 只批准 normalized Eagle3 + configured static K；plain Eagle、dynamic K、Graph/Async 等在任何 materialize 前拒绝。
- proposal-entry `L0` 是 full exact、pre-rejection；`H=L0+K`；`S` 在 proposal 内冻结。
- first pass 为 Draft 构造独立 metadata，Target metadata保持 identity/content；每个 AR step 使用真实 `E_s`，
  并从 canonical FullSource重新materialize，绝不使用上一步 Window作 source。
- P3 runtime 增加 Eagle3-only serialized step continuation：同 proposal 的 step identity递进，每次 forward 后 retire。
- future-column、poisoned previous workspace、rejection、stale step、same-row replacement、ABA 均有 CPU oracle。
- review-fix 将 continuing/terminal pure scheduler-prefill 都改为 baseline bypass，mixed仍拒绝；补齐真正定义
  `E_s` 的三个 Triton kernel drift hash，并证明 FIA exact carrier不使用 planning upper。

Node133/A2 上的单请求 NPU证据只覆盖精确 route；它不能关闭 general `G-AR-STEP`。

## 9. DeepSeek review 对最终代码的关键影响

| Phase | 关键 finding | 最终处理 |
|---|---|---|
| P1 | normalization、warning scope、factory parity、geometry test与DFlash2“eligible≠enabled”歧义 | 修正真实 bug/测试；保留 DFlash2 仅进入资格层，不启 runtime |
| P2 | FlashComm env 可绕 Gate、pointer不是freshness、Eagle3 offset自证 | 加 env Gate、冻结 mapping_epoch requirement、独立 configured-K检查 |
| P3 | Target 参数可省略、slotted nested alias、epoch provenance/hot D2H/consumer validation | Target mandatory + slots audit；production provenance、single validation、D2H留给 P4关闭 |
| P4a | profile/dummy/prefill启动路径、NumPy alias、vendor-local parity/drift、Target非空 | baseline bypass、双边 alias audit、differential/drift tests；NPU性能仍 OPEN |
| P4b | continuing chunked prefill abort、FIA exact carrier证据、kernel drift guard、rejection边界文档 | pure prefill全 bypass；exact-vs-upper tests；三个kernel hash；保留 Frozen逐step fail closed |

没有 review finding 要求改写 Frozen read/write architecture；没有 Architecture Escalation。

## 10. 本地静态/CPU证据

Final P4b Notes 记录：

- P4b targeted：`31 passed`；P4a targeted：`40 passed`；
- P1–P4b + backend/BlockTables/attention：`367 passed, 23 subtests passed`；
- locally runnable `tests/ut/spec_decode`：`470 passed, 13 skipped, 2 subtests passed`；
- full `tests/ut/spec_decode`：`472 passed, 13 skipped, 7 failed, 2 subtests passed`；
- 7 个 failure 是既有 VWN host `Invalid attention backend for None` 环境失败，不能写作 PASS；
- Ruff、format、targeted Mypy、compileall、diff-check 和可执行 hooks 通过；不可执行/网络受限项没有伪报 PASS。

Freeze package与 GitHub clean-room恢复此前已验证 exact Final tree；本轮未重新运行 production tests，
而是对最终源码、Git lineage、freeze artifacts和server evidence做收敛总结。

## 11. P0–P4 五层状态矩阵

状态层含义：`IMPLEMENTED`=production code存在；`STATIC_VERIFIED`=CPU/static contract已验证；
`NPU_VERIFIED`=仅在写明的精确route有NPU证据；`SUPPORTED_SCOPE`=当前可对外承诺的范围；
`RELEASE_READY`=release必需项全部关闭。

| 能力 | IMPLEMENTED | STATIC_VERIFIED | NPU_VERIFIED | SUPPORTED_SCOPE | RELEASE_READY |
|---|---|---|---|---|---|
| policy / forced-OFF | YES | PASS | N/A | 内部基础 contract | NO |
| Window integer math | YES | PASS | P4b间接覆盖 | Frozen数学 | NO |
| inventory / FullSource / valid counts | YES | PASS | P4b L3 active-row 852/852 | exact candidate内部能力 | NO |
| workspace / lease / mapping_epoch / store | YES | PASS | lifecycle happens-before仍OPEN | serialized eager内部能力 | NO |
| DFlash | YES | PASS | OPEN | static candidate only | NO |
| eligible DSpark | YES | PASS | OPEN | static candidate only | NO |
| Eagle3 static-K | YES | PASS | PASS：Node133/A2单请求K3/W64/TP1 eager，L3+L4 | 单请求 evidence scope；general Gate OPEN | NO |
| pure scheduler-prefill | baseline bypass | PASS | P4b测试前置经过 | 不属于Window ON支持 | NO |
| mixed prefill/decode | rejection已实现 | PASS | 已观察 EngineCore abort | UNSUPPORTED；blast radius未修 | NO |
| Graph | fail-closed | PASS negative Gate | BLOCKED | UNSUPPORTED | NO |
| Async | fail-closed | PASS negative Gate | BLOCKED | UNSUPPORTED | NO |
| Prefix cache | fail-closed | PASS negative Gate | BLOCKED | UNSUPPORTED | NO |
| TP/CP/SP/FlashComm | fail-closed | PASS negative Gate（TP2等） | BLOCKED | TP1 only candidate | NO |
| DSA/SFA/MLA/V4.1 | fail-closed | PASS capability Gate | NONE | UNSUPPORTED | NO |
| recycling/native/multi-group | fail-closed | PASS capability Gate | NONE | UNSUPPORTED | NO |

机器可读明细见 `P0_P4_Final_Gate_Status.csv`。

## 12. Runtime Evidence Decision Table

| Claim | Server verdict | Local source compatibility | Final decision |
|---|---|---|---|
| P4a DFlash/DSpark Window ON NPU | NOT_EVIDENCED | source已实现且static green | **OPEN**；GLM TP8 OFF smoke不是替代证据 |
| P4b Eagle3 single request | L3+L4 PASS | L0/K/H/S/E_s、FullSource、exact carrier与源码一致 | **PASS only for Node133/A2, K3/W64, TP1 eager single request** |
| controlled multi-request pure decode | INCOMPLETE；4种构造均未形成batch>1 | source有fingerprint/reorder protections，但未runtime触达 | **OPEN**；不得外推 |
| sequential same-engine isolation | PASS，A→C→A | epoch/fingerprint/retire设计兼容 | **PASS as sequential evidence**，不是并发batch证明 |
| write/Target isolation | PASS，84/84 before==after | Frozen边界和alias guard一致 | **PASS for observed route** |
| independent slot oracle | INCOMPLETE | static tests证明full carrier；trace被截断 | **OPEN** |
| FIA operator inputs | L4 PASS，33/33 Draft kv length==visible exact | explicit exact seam一致 | **PASS at operator-argument level** |
| physical kernel read-set | NOT_OBSERVED | 无本地直接反证 | **OPEN；Level 5缺失** |
| device lifetime happens-before | OPEN | CPU lease不等于NPU stream completion | **OPEN** |
| mixed EngineCore behavior | UNSUPPORTED_WITH_ENGINE_ABORT | source在mixed proposal hard reject | **BLOCKED for general serving**；需改为提前安全拒绝或实现支持 |
| negative Gates | 5/6 confirmed；dynamic-K NOT_RUN | source明确fail closed | **PARTIAL runtime evidence** |
| R4 performance | NOT_RUN | static不能代替profiler | **OPEN** |
| P5 readiness | design preflight READY；Graph ON BLOCKED | Graph Gate仍在P2/P4前拒绝 | **P5 design READY / production Graph BLOCKED** |

Node101/A3 的三份预期报告不存在；A3 状态是 **UNKNOWN**。不得将 Node133/A2 结论扩大到 A3。

## 13. Product Scope Decision（Owner 必须选择）

### Option A：继续要求一般 multi-request / general serving

需要完成：

- 支持或重新设计 mixed prefill/decode batch；
- 消除运行期 `NotImplementedError -> EngineDeadError` 的 service-wide abort；
- 明确 scheduler/admission 策略，验证两个及以上 active request 的 pure-decode formation；
- NPU验证 reorder、finish/add、same persistent row replacement、persistent row reuse 和 request isolation；
- 重新执行 independent slot oracle、device happens-before、Level 5 read-set与R4性能；
- 对长prompt、block crossing、rejection、future-column进行多请求组合验证。

风险是 scheduler、EngineCore failure policy、batch phase混合和设备生命周期会扩大工作面；工期需由owner评估。

### Option B：首版只支持 single-active-request exact route

这不是当前工程自动作出的产品决定，必须 owner/maintainer 明确批准。批准后仍必须：

- 在请求进入可能形成mixed batch之前安全拒绝，而不是等proposal阶段杀死EngineCore；
- 通过 `max_num_seqs`/admission policy 或等价机制保证 single-active-request；
- 给 Gate 改成明确 scoped 名称，例如 `G-AR-STEP-SINGLE-ACTIVE-A2-TP1-EAGER`；
- support matrix、用户文档、错误消息、配置检查和NPU回归全部写明 exact route；
- 不得静默删除原 general multi-request 验收项；它应转为显式 deferred requirement。

在 owner 决策前，本报告保持 general `G-AR-STEP=OPEN` 和 release HOLD。

## 14. 风险与 Open Gates

1. `G-GQA-EAGER`：P4a 无 NPU Window ON run。
2. `G-AR-STEP`：单请求证据通过，但多请求、row reuse、strict reorder 未完成。
3. Level 5：没有 kernel/profiler physical read evidence。
4. Lifetime：NO_SYNC equality 不是 reader/overwrite happens-before证明。
5. Mixed：当前会停止整个EngineCore，是产品级blocker。
6. Graph/P5：只允许design/preflight；Graph ON必须继续fail closed。
7. Async、prefix、parallel、complex backend：均未打开。
8. Node101/A3：UNKNOWN。
9. R4：性能、D2H/H2D、latency未测。
10. Release：owner acceptance、mandatory matrix和上述runtime gates未闭合。

## 15. 后续开发者阅读顺序

1. 本文与 `MRV2_Draft_Window_P0_P4_Evidence_Decision_Log.md`。
2. `MRV2_Draft_Window_P5_P8_Entry_Baseline.md`。
3. Frozen Design（只读）与 Implementation Plan 的最新 Addendum。
4. `spec_decode/__init__.py::init_speculator()`。
5. `draft_window.py`：policy/math → inventory/source/provider → generation/workspace/lease/store。
6. `draft_window_eager.py`：epoch、phase classifier、single validation、P4a metadata seam。
7. DFlash 与 DSpark `set_attn()/propose()`。
8. `draft_window_eagle3.py`：frozen proposal、per-step lifecycle。
9. AR speculator `_prefill/_multi_step_decode/_build_draft_attn_metadata/_generate_draft`。
10. `attn_utils.py`、`attention/utils.py`、`attention_v1.py` 的 explicit exact carrier。
11. 对应四个主要测试：`test_draft_window.py`、`test_draft_window_runtime.py`、
    `test_draft_window_eager.py`、`test_draft_window_eagle3.py`。
12. Server final report与 Evidence Index；不要跳过limitations。

## 16. 后续工作的唯一入口

P5–P8 不得从 superseded upstream hook prototype或debug commits开始。production branch起点是：

```text
vLLM        84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM-Ascend 1011e2c2fa99729a46efde5b5bbaf6daed975a2c
tree        7d165d585755766e7493e02f0281598e4aca3602
branch      feature/p4b-eagle3-static-k
```

P5 可开始设计与source preflight，但不得开启production Graph。详细入口契约见
`MRV2_Draft_Window_P5_P8_Entry_Baseline.md`。

## 17. 最终 Verdict

```text
P0–P3 PRODUCTION: PARTIAL

P4a STATIC: PASS
P4a NPU: OPEN

P4b STATIC: PASS
P4b SINGLE-REQUEST NPU: PASS
P4b MULTI-REQUEST NPU: OPEN

P0–P4 REQUIRED DELIVERY: PARTIAL

P5 DESIGN ENTRY: READY
P5 PRODUCTION GRAPH ENABLE: BLOCKED

FEATURE RELEASE: HOLD
```

这份结论允许后续 P5 design work，不允许把 Feature 标记为 release-ready。
