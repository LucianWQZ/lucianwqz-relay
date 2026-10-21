# MRV2 Draft Sliding Window — P7-X Independent Non-Graph Completion Review

- Reviewer: DeepSeek（Independent Reviewer；未修改 production / tests，无 commit，未登录 Node101，未运行 NPU，未读取或假造 Report1）
- Date: 2026-10-15
- 事实源：exact production source + parent→implementation diff + 我自建的执行探针与测试复现。Codex 的 Manifest / Notes / Matrix / Test 数字仅作为被审计对象。
- 本轮唯一新建产物：本文件。

---

# 1 Executive Verdict

```
P7-X REVIEW: APPROVE WITH REQUIRED FIXES
（无 production 代码缺陷；Required 项为交付物/Register/一项 owner 决策）

P7-X PRODUCTION WIRING:            FACTUAL
CAPABILITY MATRIX:                 NEEDS CORRECTION（仅 3 处文档/状态口径，状态值本身无过度声明）
TP16 STATIC CONTRACT:              PASS
DSA-CP STATIC CONTRACT:            PASS（+ 需补 window-OFF 证据口径，见 M-01）
ASYNC STATIC/LIVE BINDING:         PASS（NPU event ordering 与容量策略为 REPORT1/owner）
PREFIX STATIC CONTRACT:            PASS
CHUNKED/MIXED STATIC CONTRACT:     PASS
MULTI-REQUEST STATIC CONTRACT:     PASS
TARGET/WRITE INVARIANTS:           PASS
FORCED-OFF POLICY:                 PASS
GRAPH FREEZE:                      PRESERVED
vLLM:                              UNCHANGED
MRV1:                              UNCHANGED
REPORT1 ASSUMPTION REGISTER:       NEEDS ADDITIONS（3 条组合假设缺失）
READY FOR CODEX ADJUDICATION:      YES
```

本节结论的实质：P7-X **确实把六个 workstream 接到了真实 production consumer**（不是“去 Gate + 加 types + 加测试”），我在源码层面逐条追到了 10 个 wiring 问题（§5–§13）；**未发现 Critical**；发现 2 个 Major（一个是共享路径变更的 scope/证据口径，一个是 async 压力下的 EngineCore 级错误策略）与 10 个 Minor（文档/死代码/缺失假设行）。**没有任何 Required Fix 需要改动 production 代码。**

---

# 2 Exact Reviewed Identity（独立核对，非抄 Manifest）

| 项 | 期望 | 实测 |
|---|---|---|
| vLLM HEAD / tree | `84030bbe…` / `f3e320f8…` | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`，`git status --porcelain -uall` 空 ✓ |
| P7-X parent | `4753742ab181920292c504a79eedecf9b428ae1b` | 一致 ✓（`git log --graph` 单父链 ✓） |
| P7-X implementation | `7e88db6ed31e7965f526ea6f49cc17101f4a65b4` | HEAD ✓ |
| expected tree | `71800e2e250f0b4dc51aede643eebff55e39b404` | `git rev-parse HEAD^{tree}` = 一致 ✓ |
| branch | `feature/p7x-nongraph-completion` | 一致 ✓，工作区 clean ✓ |
| commit 数 | 单一实现 commit | 1 ✓（`feat(spec-decode): complete mandatory non-Graph draft windows`） |

---

# 3 Diff Scope

我自行计算（`git diff --stat/--name-status 4753742..7e88db6`）：

```
13 files changed, 1879 insertions(+), 100 deletions(-)
```

与 Manifest 声称的 **13 / +1879 / −100 完全一致** ✓。

生产代码 7 个（2 新 + 5 改），测试 6 个：

```
A vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py   (+525, 新模块)
M vllm_ascend/worker/v2/attn_utils.py                          (+11/-2)
M .../spec_decode/draft_window.py                              (+178)
M .../spec_decode/draft_window_async.py                        (+93)
M .../spec_decode/draft_window_eager.py                        (+155/-29)
M .../spec_decode/draft_window_eager_capability.py             (+18)
M .../spec_decode/draft_window_eagle3.py                       (+65/-9)
```

Graph 相关文件命中检查：`git diff --name-only | grep -i "graph|aclgraph|cudagraph"` 仅命中 `draft_window_nongraph.py`（文件名含 "graph" 子串）与对应测试 ✓ → **capture / provider / manager / Gate 文件零改动** ✓。

---

# 4 Scope Compliance

Owner 要求的 Non-Graph workstreams 与交付物对照（状态取自源码，非文档）：

| Workstream | 交付物 | 我的判定 |
|---|---|---|
| TP16 / ordinary TP>1 | `runtime_context.tensor_parallel_rank` + fingerprint `tensor_parallel_rank`/`parallel_read_semantics` + TP 从 gate 的 parallel 循环中移除 | 已交付，SOURCE_PROVEN（§5） |
| DSA-CP | `_provider_kind` DSA_CP_NATIVE_SWA + `attn_utils` 共享 kwargs 修复 + ratio 门 | 已交付（§6），并修复了一个**真实的既有崩溃**（§16 红绿复现） |
| Async | `DraftWindowNPUEventCompletionToken` + 池生产化 + `bound_metadata` 生命周期 + `reclaim_completed` | 已交付（§7） |
| Prefix cache | 移除 P7 的 `prefix_caching → FAIL_CLOSED`；改为 canonical source + persistent valid counts | 已交付（§8） |
| Chunked prefill | `DraftWindowRowPhase` 三态 + terminal 放行 | 已交付（§9） |
| Mixed prefill/decode | 逐行 full/window 描述符 + full-width workspace；**删除无条件 `NotImplementedError`** | 已交付（§10） |
| General multi-request | `row_phase_fingerprint` 进入 generation identity + epoch 内 phase 不变校验 | 已交付（§10） |
| Backend generalization（GLM/Qwen） | DSA 家族 + `UNRESOLVED → REPORT1` 无 dense fallback | 已交付（§11）；GLM 实际组合仍 REPORT1 ✓ 与 Manifest 一致 |

Graph：本 commit 未触及 ✓；`COMPATIBILITY/310P` 与 Graph 模式仍在 allocation 之前拒绝 ✓。

---

# 5 TP / Parallel Review

**结论：`APPROVE_STATIC`。claim “ordinary TP uses replicated logical Window read semantics” 在 source 层面成立，但 NPU per-rank actual operand 仍未验证（已由 R1-TP-01/02 覆盖）。**

## 5.1 逐条（§7 A–G）

| 问题 | 源码事实 | 判定 |
|---|---|---|
| A 每 rank 是否拥有等价 logical request sequence | `InputBatch`/`req_ids`/`idx_mapping`/`num_scheduled_tokens` 由 scheduler output 构造（`vllm/v1/worker/gpu/model_runner.py:1180-1217`），TP 不改逻辑序列；`block_tables.append_block_ids` 使用 scheduler 给出的同一 block id（`:1134-1143`） | 成立（SOURCE_PROVEN） |
| B Draft block table 是 process-local but logically replicated，还是 rank-local projection | `BlockTables` 是进程本地对象，但其**行内容是同一逻辑 block id 序列**；TP 只在 block 内部按 head 分片 KV 张量，不改 block id/行宽/长度 | replicated ✓（无 rank 分片投影） |
| C seq length 是否相同 | `seq_lens`/`num_computed_prefill_tokens` 由同一 request state 在每 rank 上重建（`states.py:106-121`），TP 不参与其计算 | 相同 ✓ |
| D backend 内部是否再次做 rank mapping | 窗口路径把 canonical `block_tables` 与逐行 `seq_lens` 交给 Ascend builder（`draft_window_eager.py:463-505` 的 `builder_kwargs`），TP 相关分片发生在 KV 张量布局层，不改变 block id | 不改变逻辑读表 ✓ |
| E 是否有拓扑模式被 ordinary TP 错误归类 | gate 逐项拒绝 DP/PP/PCP/DCP>1、SP、FlashComm(除非 DSA-CP)、DSA-CP-无-provider（`draft_window_nongraph.py:486-507`）；PCP 亦通过 `prefill_context_parallel_size` 被拒 | 无 ✓；**但见 m-08（TP×async 组合缺假设行）** |
| F TP rank authority 真实来源 | `_get_tensor_parallel_rank`：`parallel_config.tensor_parallel_rank` 若存在→用之；否则 world==1→0；否则 `get_tp_group().rank_in_group`；解析失败 **raise**（`draft_window.py:1405-1426`）。我实测 `grep -rn tensor_parallel_rank vllm/` → **pinned vLLM 中不存在该属性** → 生产恒走 `get_tp_group()`，**不存在 rank-0 兜底** ✓（tests 通过显式配置字段注入，属允许的显式注入） | 正确 ✓（SOURCE_PROVEN） |
| G full slot/write 是否仍来自 canonical BlockTables | `slot_mappings=self.block_tables.slot_mappings[:, :num_tokens_padded]`（`draft_window_eager.py:498`；Eagle3 同构 `autoregressive/speculator.py` 的 `slot_mappings=self.block_tables.slot_mappings[...]`）；typed inputs 明确不含 slot/positions | 成立 ✓ |

## 5.2 无 `V/world_size` 分割
窗口数学只使用 absolute `[S,E)`（§1 设计），P7-X 未引入任何按 world size 除法 ✓；DCP helper 仍只做 `local(E)-local(S)` 且在 DCP>1 时被 REPORT1 拦住 ✓。

**NPU 未验证项（保留 REPORT1/NPU）**：per-rank Draft table/length 实际 operand、per-rank slot/cache 写入、TP16 输出一致性。

---

# 6 DSA / DSA-CP Review

**结论：`APPROVE_STATIC`（uncompressed, single gid）；compressed 被正确 `SOURCE_BLOCKED`；DSA-CP 无自造投影。**

## 6.1 Actual builder identity（执行验证，非 fixture 猜测）
`AscendDSABackend.get_builder_cls()`（`attention/dsa_v1.py:222-240`）在 `enable_dsa_cp()` 时返回 `vllm_ascend.attention.context_parallel.dsa_cp.AscendDSACPMetadataBuilder`，在 `enable_pcp()` 时返回 `AscendDSAPCPMetadataBuilder`，否则 `AscendDSAMetadataBuilder` ✓ —— 与 P7-X `_provider_kind`（`draft_window_nongraph.py:327-340`）使用的类完全一致。

我额外验证了两个易错点：
- `AscendDSACPMetadataBuilder(AttentionMetadataBuilder[AscendDSAMetadata])`（`dsa_cp.py:188`）**不是** `AscendDSAMetadataBuilder` 子类 ✓ → P7-X 用 `isinstance` 双类匹配是正确的；
- `AscendDSAPCPMetadataBuilder(dsa_v1.AscendDSAMetadataBuilder)`（`dsa_cp.py:2141`）**是**其子类 → 会被分类为 DSA_NATIVE_SWA，但 PCP≻1 先被 parallel 门拒绝 → REPORT1 ✓（无“PCP 被当成普通 DSA”这一漏洞）。

## 6.2 Read pipeline 与 derived state
窗口把 canonical kernel-block 表 + 逐行 exact/upper 交给真实 builder（§6.1）；DSA 的 local lengths / query ranges / indices / SAS / native SWA / compressor / QLI / 通信 state 由 builder 自行派生（`dsa_v1.py:873-1072` 的 SAS/QLI/CMP 分支），P7-X 不注入第二套投影 ✓。**“hidden full-state bypass”专项**：我在 `draft_window_nongraph.py` 与 DSA 相关改动中未找到任何从 canonical full seq len / canonical full table / Target metadata **重新派生** read 长度的代码；长度唯一来源是 `provider.describe(...)` 的 scalar plan + `build_prefix_resident_snapshot` 的 valid counts（均来自 canonical FullSource，经 descriptor fingerprint 进入 generation identity）✓。

## 6.3 Compression gate
`build_draft_window_inventory` 从**真实 builder 实例**读取 `compressor_ratio`（`draft_window.py:1069-1074`；属性确实存在于 `dsa_v1.py:664` 与 DSA-CP builder，后者还在 `build_for_drafting` 断言 `<=1`，`dsa_cp.py:427`）→ `ratio > 1 → SOURCE_BLOCKED`、`ratio 缺失 → REPORT1`（`draft_window_nongraph.py:433-447`）。两者都发生在 `require_local_materialization()`（`:148-156`）**之前**，而后者在 `build_full_draft_kv_source`/workspace 之前 raise（`draft_window.py:1457-1465`）→ **先建 partial state 再报错的情形不存在** ✓。

## 6.4 DSA-CP 是否自造 CP projection
没有：窗口只提供 common table/exact/upper；CP-local 派生由 builder 负责（`dsa_cp.py:822-1057`），P7-X 未新增 local range 计算，也未改 full slot map ✓。

## 6.5 ⚠ 共享路径变更（M-01）
`attn_utils.build_attn_metadata` 的 `is_dsa_builder` 由 `AscendDSAMetadataBuilder` 扩为 `(AscendDSAMetadataBuilder, AscendDSACPMetadataBuilder)`（`attn_utils.py:344-352`）。该函数是**非窗口路径也使用**的共享生产助手（`AscendModelState.prepare_attn` → 它）。我在父提交用 P7-X 的测试复现了 red（§16.3），确认这是**修既有崩溃**而非回归；但它是“Draft Window”commit 内的**无窗口门控**共享行为变更 → 见 M-01。

---

# 7 Async Review

**结论：`APPROVE_STATIC`；真实 NPU stream ordering、event 可见性与 backend late reader 保持 NPU 要求（R1-ASYNC-01）。**

## 7.1 生产调用链（逐环已验证）

```
proposal scope (draft_window_eager.py:308-360)
  → async_pool.reclaim_completed()            # 非阻塞 poll/retire/release
  → async_pool.acquire(mapping_epoch, ordered_ids, phase, step)   # 最小空 lane
  → (forward 内) materialize → bind(publish) → read_bound_metadata
  → finally: factory() = DraftWindowNPUEventCompletionToken.record_current_stream()
  → async_pool.submit(handle, completion):  mark_reader_pending → retire_generation
  → 之后由 reclaim_completed()/poll() 以 event.query() 判完成 → retire → release
```

- **谁产生 state**：mixin state init 在 `topology.async_scheduling` 为真时创建池（`draft_window_eager.py:257-275`），其 topology 来自 capability 的 `eager_topology_fingerprint`。
- **backing 归属**：每 lane 一个独立 `DraftWindowRuntimeState`（每 lane 独立 workspace/lease/store，`draft_window_async.py:88-98`），我执行验证过 lane 间 backing 地址互异、释放后同址复用但 generation_id 递增（P7 审查探针）。已有测试 `test_stable_lane_backing_survives_a_b_a_without_stale_generation` 覆盖同一性质 ✓。
- **metadata 生命周期**：`handle.bound_metadata` 在 P3 store 因 pending retirement 被 discard 后仍持有 Draft-private metadata 与 derived buffers，直到 `release` 清空（`draft_window_async.py:91-95, 289-292, 365`）→ 覆盖“P3 store 不能做 async 生命周期 owner”这一缺口 ✓（这正是 P7 `AttributeError` red 的对象，见 §16.2）。
- **没有 hidden serialization**：`reclaim_completed` 只对 `SUBMITTED` 且 `poll()` 返回 True 的 handle 操作；`poll` 走 `event.query()`（非阻塞，`draft_window_async.py:69-73`）；proposal 结束不等待 event ✓；pressure 时直接报错而不等待（§7.4）。

## 7.2 Event 是否记录在真正最后 reader 之后（§9.1）
`record_current_stream` 在 proposal 的 finally 中、Draft forward 已提交之后记录当前 NPU stream 的 event（`draft_window_async.py:75-83`）；同 stream 内该 event 有序于此前提交的 Draft 算子 ✓ **SOURCE_PROVEN**。但仍有两类未由源码证明的 late reader：HCCL/通信 stream（TP>1 或 DSA-CP 组合）与任何 backend 自持 stream → 属 **NPU_REQUIRED**（不判 bug；且 async+DSA/DSA-CP 已被 REPORT1 拦住，async+TP>1 仍开放 → 见 m-08）。

## 7.3 Abort 全分支（我逐分支读过并已在 P7 探针执行过等价场景）
| 分支 | 行为 | 判定 |
|---|---|---|
| before materialize (ACQUIRED) | `abort` → RETIRED（无 inputs 可 abort）；随后 `release` | ✓ 无提前 free |
| after materialize/bind, before submit | `abort_generation` + 清 metadata/buffers → RETIRED → release | ✓ |
| after submit (SUBMITTED) | 仅置 `abort_requested`，**保持 lane/backing**，必须等 `event.query()` 完成 | ✓ 绝不提前 free |
| completion-query failure | `submit` 捕获后保持 SUBMITTED 供 `poll` 重试；`poll_reader_completion` 依赖 `_active_inputs` 未被清（`_retire_lease` 在 `_lease_pool.retire` 抛错时不执行 `_active_inputs=None`）✓ | ✓ 不推断完成 |
| pool pressure | `RuntimeError` → 见 M-02 | ⚠ 策略项 |

## 7.4 Pressure（M-02）
`acquire` 找不到空 lane 即 raise `RuntimeError("draft-window async pool pressure: all N lanes are owned")`（`draft_window_async.py:172-176`），异常沿 proposal scope 上抛到 EngineCore。默认容量来自 `additional_config["draft_window_async_lanes"]`（默认 2，`draft_window_eager.py:266-269`）。→ M-02。

## 7.5 边界（§10/§11）：Eagle3 / DSA / DSA-CP async 是否被误开
- Eagle3 + async：gate 最先返回 `REPORT1_RUNTIME_DEPENDENT`（`draft_window_nongraph.py:404-410`），`require_local_materialization` 随后 raise → **capability 从未构建** → mixin 的池初始化不可能发生 ✓ **未误开**。
- DSA/DSA-CP + async：`:448-454` 同样在 materialization 前 REPORT1 ✓。
- 池初始化本身就要求 `topology.async_scheduling` 且 topology 非空，而 topology 只在 LOCAL_STATIC_READY 时产出 → 自洽 ✓。

---

# 8 Prefix Cache Review

**结论：`APPROVE_STATIC`；eviction/reuse 的真实物理行为与多请求共享前缀属 REPORT1（R1-PFX-01）。**

1. **Source validity**：valid block 数来自 `gather_valid_num_blocks_cpu` 读 **canonical CPU owner**（`_persistent_num_blocks_cpu`，按 `idx_mapping` 选行；`draft_window.py` 内该函数 docstring 明确“UvaBackedTensor 的 accelerator 视图是轮转传输，不是稳定 freshness 身份”）→ 这是**该请求已分配的持久 block 计数**。它是否等于“物理 resident extent”？——我逐项排查了仓库里唯一的“非 resident”机制：`sparse_kv_offload_config` 只被 **SFA/sparse** 路径消费（`attention/sfa_v1.py:276,296`、`sfa_kv_offload.py`、`distributed/kv_transfer/sparse_kv_offload/*`），而 SFA 在 P7-X 中恒为 `UNRESOLVED → REPORT1_RUNTIME_DEPENDENT` ✓ → **对已放行 route（dense/DSA），allocated == resident** ✓。因此 §12.1 的漏洞在当前源码中**不成立**（结论为 SOURCE_PROVEN + 依赖：一旦将来把 SFA/offload 纳入 provider，就必须引入真正的 resident-set provider）。
2. **Eviction / reuse（§12.2）**：block id 复用只可能发生在 cache manager 释放引用之后；窗口的 freshness 由 `ordered_request_fingerprint + mapping_epoch + idx_mapping contents + source_identity + valid counts + row_phase` 共同承担（`DraftWindowResidentSetSnapshot` 字段 + generation identity），旧 generation 的 metadata 在 publish/read 时会因 identity 不匹配被拒 ✓。**但**“同一 owner allocation 中 block id 被回收再分配”的物理观测无法由 host 静态证明 → 保持 REPORT1/R1-PFX-01 ✓（他们的分类正确）。
3. **Reader lifetime（§12.3）**：窗口读的是请求自身持有的 KV block（引用计数在请求生命周期内有效），**不是** Window workspace 的生命周期；P3 lease 只保护 workspace backing。二者不可混淆——P7-X 文档 `P7X_Prefix_Prefill_Spec.md` 已明确区分 ✓（我未发现把 workspace lifetime 当作 KV block lifetime 的编码）。
4. **死 API（m-03）**：`DraftWindowResidentSetSnapshot.validate_expected` 在生产中无调用（仅 `tests/ut/spec_decode/test_draft_window_nongraph.py:241`）。

---

# 9 Chunked Prefill Review

**结论：`APPROVE_STATIC`；phase 分类与 pinned 语义一致，且是**前置**（pre-step）计数语义。**

我将 `classify_draft_window_batch_phase`（`draft_window_nongraph.py:159-209`）与 pinned 上游逐项对照：

| 分类依据 | 上游事实 | 判定 |
|---|---|---|
| `num_computed_prefill_tokens_np` / `prefill_len_np` / `is_prefilling_np` / `has_prefill` 字段存在 | `vllm/v1/worker/gpu/input_batch.py:81-87`，且注释明确 `is_prefilling_np == (num_computed_prefill_tokens_np < prefill_len_np)`、`has_prefill == np.any(is_prefilling_np)` | 与实现的交叉校验（`:182-186`）**逐字一致** ✓ |
| computed 是 before-step 还是 after-step | 批状态构造读 `req_states.num_computed_prefill_tokens[idx_mapping]`（`model_runner.py:1196`，为 `np.minimum(num_computed_tokens, prefill_len)`，`:1145-1150`），其值来自 scheduler 的 `scheduled_cached_reqs.num_computed_tokens`（`:1134-1139`，执行前快照）；且该 numpy 数组是**fancy-index 产物（副本）**，postprocess 之后的更新不会回写进 InputBatch 快照 | **pre-step 语义** ✓ → `computed + scheduled < prefill_len` 判 CONTINUING、否则 TERMINAL 与“本步是否完成 prefill”一致 ✓ |
| scheduled 是否含 bonus/spec token | 对该分类**无影响**：CONTINUING 分支只在 `actual_prefill=True`（即真正的 prefill 行）时使用 scheduled，而 adaptive verification 的“upper bound”语义只作用于 decode 行（其 `computed == prefill_len` → PURE_DECODE，不读 scheduled）✓ | 无影响 ✓（含混风险已排除） |
| 空/填充行 | 分类仅取 `[:num_reqs]`（忽略 padding 行 ✓）；`total_num_scheduled_tokens == 0` 时 runner 在调用 speculator 前直接返回（`model_runner.py:1598-1605`）→ 空批次不可达 ✓ | 无空洞 ✓ |
| mixed scheduling | 三态逐行判定 + `batch_phase` 归纳（MIXED）✓ | ✓ |

`epoch_source.validate` 额外要求同一 epoch 内 phase plan 不变（`draft_window_eager.py:135-141`）✓。

---

# 10 Mixed / Multi-request Review

**结论：`APPROVE_STATIC`；`NotImplementedError` 已消除；行级 full/window 共存与 batch-global builder 风险已登记（R1-MIX-01），实际 batch-global 语义仍需 NPU。**

## 10.1 A–E 逐问
| 问题 | 源码事实 | 判定 |
|---|---|---|
| A 一个 common metadata 能否表达 row A full + row B window | 可以：表的**行宽是全局**（`block_tables` 每行独立），读长度是**逐行张量**（`seq_lens`/exact/upper）；窗口行把 `[S,E)` 列拷到行首 0..V-1 并置 `seq_lens=V`，continuing 行拷 `valid` 列并置 `seq_lens=full_exact`（`draft_window_nongraph.py:265-310`） | 结构成立 ✓ |
| B builder 是否把 `is_prefilling`/`max seq length`/query layout/causal 当全局状态 | dense(DFlash/DSpark) 路径**不传** `is_prefilling`，draft query layout 恒为 uniform(K+1/K)；Eagle3 first-pass 传**per-row** `is_prefilling_np` 且 `attn_state` **继承 Target 层**（`autoregressive/speculator.py` 的 `_build_eagle3_private_attn_metadata`），AR step 恒 `DecodeOnly`（uniform 1 query ✓）。`max_query_len`/`causal` 为 batch-global，但两者在混合批中均由 uniform draft 布局导出 | 未见全局相位假设被违反 ✓；**实际算子行为仍属 REPORT1** |
| C 不同 row 的 table width/padding | workspace 统一为 **full source row width**（`draft_window.py:1499-1506`），每行 active columns 独立记录，尾部与 padding 行被重置 ✓ | ✓ |
| D continuing row 是否会被 Window max/read cap 影响 | continuing 行走**独立分支**：`required_columns=valid`、`visible=full_exact`、`S=0`，并在 `safe_extent < full_exact` 时硬失败（`draft_window_nongraph.py:278-292`；Eagle3 同构 `draft_window_eagle3.py:549-570`） | 不受 Window 影响 ✓ |
| E decode row 是否 silent full fallback | 无 fallback 路径：decode/terminal 行恒走 `provider.describe(...)` 的 window 描述符；若 `visible_upper < visible` 直接 raise | 无 silent full ✓ |

## 10.2 G-MIXED / blast radius（§17）
- 无条件的 `NotImplementedError("…does not support mixed prefill/decode proposals")` **已从代码中消失**（父提交 `draft_window_eager.py:579` → P7-X 改为 `bypass_entire_batch` 判定，`:673-683`）✓。
- 我确认该文件被 P7-X 修改且新实现只在“**整批都是 PREFILL_CONTINUING**”时走 baseline，其余（terminal / mixed / decode）进入行级 Window 路径 ✓。
- 失败边界：mixed 路径内的异常仍会上抛到 EngineCore（无 request 级隔离），但**不再存在针对 mixed 的无条件 raise**；per-row 不支持的组合（压缩/多组/其他后端）在 **allocation 之前** 被 gate 拒 ✓。
- 因此 §17 要求“source-level unconditional crash path must disappear” **满足** ✓；真正的 EngineCore 隔离仍需 NPU/server 证明（未宣称）✓。

## 10.3 Multi-request 生命周期
freshness 组成（我逐项确认全部进入 identity 或被显式校验）：`mapping_epoch`（严格递增，`draft_window.py:2169-2174`）、`ordered_request_fingerprint`（唯一非空）、`idx_mapping contents`（`_proposal_fingerprint` + epoch 内变化校验）、`row_phase_fingerprint`（新增字段，`DraftWindowGenerationIdentity:1542-1572` 校验长度）、`source_identity`、`provider_id/version`、`topology_fingerprint`、`execution_lane`、`phase/step` ✓。**未发现**以 row index / request count / tensor pointer 作为 freshness 的代码（`DraftWindowResidentSetSnapshot` 里的 `mapping_fingerprint` 存的是 `idx_mapping` **内容**，不是指针 ✓）。

---

# 11 Backend Provider Review

Gate 形态（`draft_window_nongraph.py:327-340, 411-424, 508-519`）：

| 布局/consumer | provider kind | 放行条件 | 实际状态 |
|---|---|---|---|
| dense GQA/FIA | `DENSE_DIRECT_PREFIX` | dense 且无 group capability failure | LOCAL_STATIC_READY |
| uncompressed DSA/SWA | `DSA_NATIVE_SWA` | builder 是 `AscendDSAMetadataBuilder` 子类 + ratio ∈ {0,1} | LOCAL_STATIC_READY |
| uncompressed DSA-CP | `DSA_CP_NATIVE_SWA` | builder 是 `AscendDSACPMetadataBuilder` + `dsa_context_parallel` | LOCAL_STATIC_READY |
| 其余（SFA/MLA/native/recycling/unknown/FA3/kpool/CP-PCP…) | `UNRESOLVED` | — | REPORT1_RUNTIME_DEPENDENT（allocation 前） |

**“unsupported 误入 positive route”专项**：我枚举了 `vllm_ascend/attention/` 全部 backend 类（与 P8 审查同表）并逐一推演 `_classify_layout` + `_provider_kind`：DSA 六个变体 → DSA ✓；ML A/SFA/indexer → 各自布局→非 dense→UNRESOLVED ✓；`AscendFABackend`/`AscendIndexerKPool*`（非 `AscendAttentionBackend` 子类）→ 由 dense group failure 拒 ✓；310P `AscendAttentionBackend310`（dense 形状）→ 由 `AttentionBackendFamily.COMPATIBILITY` 门在 FullSource 前拒 ✓；DFlash2 → 由 route 判定拒 ✓（route 名我执行验证仍是 `dflash2`）。**未发现 class inheritance / isinstance 宽匹配 / unknown fallback 造成的误放行** ✓ → 与 `P7X_Backend_Provider_Matrix.md` 一致 ✓。

---

# 12 Method / Forced-OFF Review

全部基于源码顺序（非文档）：

| 场景 | 事实 | 判定 |
|---|---|---|
| CONFIG_OFF | `resolve_draft_window_policy` 返回 CONFIG_OFF → `init_speculator` 直接走 baseline 并 return（`spec_decode/__init__.py`）→ `_configure_draft_window` 未调用 → `_initialize_draft_window_source_capability` 因 policy 缺失立即 return（AR `:105-106`、DFlash/DSpark 同构）→ **零 P7-X 状态、零池、零 provider** ✓ | PASS |
| MTP | FORCED_OFF 在 `requested_window_size` 校验与 inventory **之前**（`draft_window.py:633-641`）；warning-once 由 `init_speculator` 产生 | PASS |
| DSV4 co-trained DSpark | 同上分支（`:643-651`，`_is_deepseek_v4_target:605-608`） | PASS |
| plain Eagle | 不在 `{eagle3,dflash,dspark}` → policy 阶段 `NotImplementedError`（配置即拒）→ P7-X 状态 `SOURCE_BLOCKED`（`draft_window_nongraph.py:353-360` 不可达，因为 policy 已拒） | PASS（无“偷偷打开”） |
| dynamic-K | gate `:390-396` SOURCE_BLOCKED；另有 `resolve_static_future_offset` 独立 raise | PASS |
| DFlash2 | gate `:397-403` SOURCE_BLOCKED（route 名执行验证为 `dflash2`） | PASS |

**Backend 能力不能覆盖 policy**：`evaluate_p7x_nongraph_capability` 对 CONFIG_OFF/FORCED_OFF 在函数最前 return（`:353-360`），后续任何 backend/topology 结论都无法把 OFF 升为 READY ✓。

---

# 13 Read/Write / Target Isolation

| 不变量 | 证据 | 判定 |
|---|---|---|
| slot mapping 仍 full/absolute | `slot_mappings=self.block_tables.slot_mappings[...]`（dense `draft_window_eager.py:498`；Eagle3 同路径）；`DraftMetadataInputs` 不含 slot/positions（P3 不变量） | PASS |
| Target metadata owner 不变 | `_require_nonempty_target_metadata` / `model_state.attn_metadata is target_metadata` 二次校验（`autoregressive/speculator.py` build 前后各一次） + `_isolate_draft_metadata_from_target` | PASS |
| positions / query layout 不变 | 窗口只改 `seq_lens/seq_lens_cpu/exact/upper/block_tables`；positions 与 query_start_loc 仍来自 `input_buffers`（dense 用 `self.input_buffers.query_start_loc[...]`） | PASS |
| typed inputs 只能带窗口读表 | `DraftMetadataInputs` 字段集（P3）本轮未扩大 | PASS |
| workspace 现在 full-width | `workspace_capacity_columns = full_source.input_block_table_row_width(gid)`（`draft_window.py:1499-1506`），并在 `build_draft_window_runtime_state` 校验 `>= provider.capacity_columns` 且 `<= source_table.shape[1]`（`:2486-2492`）；窗口行的 `required_columns` 仍受 **provider 窄容量**约束（`provider.describe`），continuing 行用 `required_columns=valid` | 见下 |

**workspace 由窄变宽是否引入 silent full read？** 我逐点排查：读长度由逐行 `seq_lens` 决定（dense 经 `read_inputs.seq_lens`、Eagle3 同），表宽只是 FIA/DSA 的 `block_table` 行宽；窗口行的列拷贝与长度仍由 descriptor 决定（active columns 逐行记录），因此**表宽**不等于**读长度** ✓。此变更的目的是让 continuing 行与 window 行共享一个稳定 backing（混合批必需）✓。属 SOURCE_PROVEN，但“表宽不参与读长度”这一后端事实在 DSA/DSA-CP 上仍应与 §6.2 的 NPU 证据一起确认（已由 R1-BE-01/DSACP-01 覆盖 ✓）。

---

# 14 Graph Freeze / Repository Boundary

| 检查 | 结果 |
|---|---|
| P7-X 是否改 graph capture/provider/manager/Gate | **否**：diff 无 `aclgraph*`/`draft_window_graph.py`/P5-P6 provider 安装点（`install_draft_window_graph_binding_provider` 仍无生产调用者）✓ |
| Graph 配置是否仍在 FullSource 前拒绝 | **是**：`evaluate_p7x_nongraph_capability:376-382` 最先返回 `GRAPH_FROZEN`，`require_local_materialization` 随后 raise（allocation 前）✓ |
| FULL / FULL_DECODE_ONLY / PIECEWISE | 三者都命中 `graph_mode != "NONE"` ✓（未新增任何 graph 分支） |
| vLLM | `84030bbe…` clean/zero diff ✓ |
| MRV1（`vllm_ascend/spec_decode/*`） | diff 中**零改动** ✓ |
| 新增全局/ContextVar/module-global transport | 无：新增状态均为实例字段（`_draft_window_async_pool`/`_draft_window_async_handle`/`_draft_window_completion_token_factory`/`bound_metadata`/fingerprint 字段）；`_get_tensor_parallel_rank` 内部延迟 import ✓；未新增 monkeypatch ✓（沿用既有 `build_attn_metadata_wrapper`，未扩大其语义） |
| site-packages / 条件式 prototype import / Target owner swap | 无 ✓ |

**GRAPH FREEZE: PRESERVED。**

---

# 15 Report1 Assumption Audit

Register 现有 14 行（R1-TP-01/02、GLM-01、QWEN-01、DSACP-01/02、PFX-01、CHK-01、MIX-01、ASYNC-01/02、BE-01、MG-01、PAR-01），每行含 local assumption / Report1 observation / falsifier / affected code / severity ✓ 结构完整、severity 合理（critical 居多）✓。

**我发现的缺失组合（§28 要求的“遗漏但同样需要服务器证明”）→ m-08/m-09/m-10**：
1. **TP>1 × async**：gate 允许 ordinary TP 与 async 同时成立（parallel 循环不含 TP；async 只对 eagle3/DSA 设限）→ dense DFlash/DSpark + TP16 + async = LOCAL_STATIC_READY，但 R1-ASYNC-01 只覆盖“当前 stream 有序”，未覆盖 **多 rank 的 event 覆盖范围与通信 stream**。
2. **prefix × async**：池初始化已删除 prefix 拒绝，gate 也不再拒 prefix → 「prefix 共享 block 的读一致性 + lane-backed workspace 生命周期」的组合无人证明（R1-PFX-01 与 R1-ASYNC-01 各自覆盖不到交叉）。
3. **ordinary TP × uncompressed DSA/DSA-CP**：DSA 的 rank-local 派生 state（SAS/local ranges/index）在 TP 复制读视图下的行为未单列（R1-BE-01 面向单 route，R1-TP-01 面向 block table/length，不含 DSA derived buffers）。

**证据分类抽查（§29）**：文档未出现“static → NPU / TP1 → TP16 / GQA → DSA / DFlash → DSpark / single → general serving / host event → NPU ordering”的继承；`P7X_NPU_Revalidation_Matrix.md` 明确要求“post-review P7-X final SHA”并要求负例（NEG-MTP/V4/CMP-DSA/GRAPH）✓；`P7X_Test_Results.md` 明确“No test result in this ledger is NPU evidence” ✓。

---

# 16 Test Reproduction（我自跑，非复制）

## 16.1 P7-X green（全部复现，数字逐项一致）
| Scope | 我做 | 文档 | 一致 |
|---|---|---|---|
| 六个 targeted 文件 | **291 passed** | 291 | ✓ |
| `tests/ut/spec_decode` | **608 passed, 13 skipped, 7 failed** | 同 | ✓（7 项为宿主机 VWN `Invalid attention backend for None`） |
| `tests/ut/attention` | **472 passed, 3 skipped** | 同 | ✓ |
| `tests/ut/_310p` | **155 passed, 2 skipped** | 同 | ✓ |
| worker/v2 + block table + attn_utils_v2 + dcp/pcp manager | **147 passed** | 147 | ✓ |
| compressed prefix cache + prefix_cp patches + GLM cache/config | **74 passed, 1 skipped** | 74 | ✓ |

## 16.2 Parent-red / P7-X-green 复现（§24，用 temp detached worktree）
方法：`git worktree add --detach /tmp/p7x-parent 4753742`，只把 **P7-X 版测试** checkout 进该 worktree（生产代码保持父版本，已核对 `git diff HEAD -- vllm_ascend/` 为空），确认导入路径解析到 `/tmp/p7x-parent/vllm_ascend` 后运行；结束后 `git worktree remove --force`：

| 项 | 我的结果 |
|---|---|
| `tests/ut/worker/test_attn_utils_v2.py`（P7-X 版）在**父提交** | **1 failed, 45 passed**，失败原因 `E KeyError: 'common_ratio_to_sas_metadata'` —— 与文档声称的 red 完全一致 ✓ |
| 同一测试在 P7-X | **1 passed**（`-k dsa_cp`）✓ |
| 其余新增/改动测试文件在父提交 | **collection error**（`ModuleNotFoundError: vllm_ascend...draft_window_nongraph`）——属“新模块尚未存在”的弱 red ✓（其行为级 red 主张我只能以源码差分存证：父提交无 `bound_metadata` 字段、`_requires_prefill_baseline_bypass` 仍对 mixed raise、inventory 无 `source_geometry_failures`/`drafting_compression_ratio`，三点均由 `git diff` 逐行确认 ✓） |

**结论**：四条 test-first 主张中，我**执行级**复现了 DSA-CP 一条（含具体异常类型）；其余三条为“新模块/新字段不存在”型 red，我用源码差分独立确认，未把文档表格当作证据。

## 16.3 未跑/环境阻塞
`tests/ut/core`、`tests/ut/worker`（全量）未跑 → **ENVIRONMENT_BLOCKED 未自证**（文档给出的原因是缺 `httpx`/NPU 私有钩子；我未复现，故不引用其分类）。`distributed` 在沙箱内会因 socket 受限失败（与 P8 审查一致），我本轮以沙箱外方式运行得 **572 passed** ✓。

---

# 17 Static Checks

我自行执行：

| 检查 | 结果 |
|---|---|
| Ruff check（5 个生产文件，含新模块） | `All checks passed!` ✓ |
| `ruff format --check`（全部 13 个改动文件） | `13 files already formatted` ✓ |
| `compileall`（`spec_decode/` + `attn_utils.py`） | OK ✓ |
| `git diff --check 4753742..7e88db6` | clean ✓ |
| Mypy | **NOT RUN**（本轮未执行；文档称 targeted mypy PASS，我未复现，不背书） |

---

# 18 Findings

## Critical
**无。** 我逐项排查了 §30 列出的全部 Critical 形态，结论均不成立：
- Target/write 被 Window 污染：slot/positions/表 owner 均未变（§13）✓
- TP16 positive path 物理语义明显错误：replicated 语义有源码依据，无按 world size 除法（§5）✓
- compressed / unsupported backend 被误开放：ratio>1 与 UNRESOLVED 均在 allocation 前拒（§6.3/§11）✓
- Graph 被意外打开：`GRAPH_FROZEN` 分支最先执行（§14）✓
- async backing 在 reader 完成前复用：状态机禁止（§7.3）✓
- mixed path silent full fallback：逐行描述符，无 fallback（§10.1E）✓
- forced-OFF route 创建 Window state：policy 先行 + capability 不构建（§12）✓

## Major

### M-01 — 无窗口门控的共享生产路径变更未在交付物中单列
- **Claim being reviewed**：P7-X 只是扩展 Draft Window 的 non-Graph 数据面，不改变其他行为。
- **Exact source**：`vllm_ascend/worker/v2/attn_utils.py:344-352`（`is_dsa_builder` 由单类扩为 `(AscendDSAMetadataBuilder, AscendDSACPMetadataBuilder)`），以及其后 `:365-372`（新增 `num_actual_reqs`/`common_ratio_to_sas_metadata` kwargs）与 `:390-392`（读回 builder 的共享 dict）。
- **Observed**：该函数由 `AscendModelState.prepare_attn`（`worker/v2/model_states/default.py`）调用，**与 draft_window_size 是否开启无关**；父提交下 DSA-CP builder 会因 `assert common_ratio_to_sas_metadata is not None`（`attention/context_parallel/dsa_cp.py:332`）而失败——我用父 worktree + P7-X 测试复现：`KeyError: 'common_ratio_to_sas_metadata'`。
- **Expected**：改动本身正确且必要（修既有崩溃）；但交付物（Manifest / Notes / Register）应把「共享非窗口路径变更」显式列为 scope 项，并为其提供**独立于窗口**的运行证据。
- **Reproduction**：§16.2 的 worktree 复现（父=1 failed/45 passed、P7-X=1 passed）。
- **Why it matters**：这是本 commit 中唯一“即使不启用 draft_window_size 也会改变 MRV2 行为”的改动；若只按“窗口功能”口径验收，遗漏了对 plain DSA-CP（window OFF）的回归证据。
- **Suggested correction**：交付物中显式记录该共享变更；NPU 矩阵新增一例 **DSACP-00（window OFF + 同 DSA-CP 组合）** 作为该变更的隔离验证；Register 增补一行（falsifier：window OFF 下 DSA-CP metadata 与父版本不一致）。
- **Needs**：REPORT1 + NPU（无需 LOCAL_FIX）
- **Release impact**：Blocking for DSA-CP release scope；不影响 dense 路由。

### M-02 — async 池耗尽在 EngineCore 路径上以 RuntimeError 终止，且默认容量为硬编码 2
- **Claim being reviewed**："pool pressure: deterministic error, never overwrite an active lane"（`P7X_Async_Lifecycle_Spec.md`）。
- **Exact source**：`draft_window_async.py:172-176`（`acquire` 找不到空 lane → `RuntimeError`）；`draft_window_eager.py:266-269`（`additional_config.get("draft_window_async_lanes", 2)`）；异常沿 `_draft_window_proposal_scope` → `propose` → runner 上抛。
- **Observed**：容量固定（默认 2）、无等待/降级/准入；只要 host 领先 device 超过容量即抛错并终止 step（EngineCore 级）。
- **Expected**：要么由 owner 明确“耗尽即硬错误 + 配置足够容量”的产品策略并给出容量上界论证，要么实现有界等待/降级（如本 step 回退同步路径）。
- **Reproduction**：`/tmp` 探针（复用 UT helper）可稳定构造三 handle 并发 → 第三次 acquire 抛 pressure；本轮我未在 NPU 上验证其真实发生概率。
- **Why it matters**：这是 P7-X 新引入的、位于**正常 async 路径**上的显式崩溃点（对齐 §30 “normal-path crash” 的 Major 示例）。
- **Suggested correction**：owner 决策容量策略；Register 的 R1-ASYNC-02 已按 major 登记 ✓（保留），但需补一句“耗尽时是否允许回退同步”的产品口径，并在 NPU 矩阵 ASYNC-PRESSURE 中给出真实 in-flight 上界。
- **Needs**：PRODUCT_DECISION + REPORT1
- **Release impact**：async release 门的必备项（非 dense 主路径）。

## Minor

- **m-01** `P7X_Parallel_Window_Spec.md` 声称 `P7EagerTopologyFingerprint` 现在包含 “K/query width, W”；实际字段集（`draft_window_eager_capability.py:39-64`）**没有** window size / num_speculative_tokens / query width。W/K 由 descriptor fingerprint + `resolve_static_future_offset` 间接钉住。→ 修正文案或补字段（LOCAL_FIX，文档）。
- **m-02** P7 的 gate 函数 `evaluate_draft_window_eager_capability`（`draft_window_eager_capability.py:234`）与 `P7EagerCapabilityStatus.READY_FOR_NPU`/`require_live_materialization` 在 P7-X 后**生产无调用者**（我 grep 确认），而 `P7X_Document_Index.md:137` 仍把 `P7_Eager_Capability_Matrix.md` 标为 `canonical-live`（其中“prefix ON → FAIL_CLOSED”已与现状相反）。→ 标注 superseded 或删除死入口（LOCAL_FIX，文档/清理）。
- **m-03** `DraftWindowResidentSetSnapshot.validate_expected` 生产无调用（仅测试 `test_draft_window_nongraph.py:241`）→ 该 API 宣称的身份校验在运行时并未执行（freshness 由其他字段承担）。→ 或在 materialize 处真正调用，或删除该断言接口（LOCAL_FIX）。
- **m-04** 新增配置键 `draft_window_async_lanes`（默认 2）未出现在任何 P7-X 文档中（我 grep 全部 `P7X_*.md` 无命中）→ 补文档（LOCAL_FIX）。
- **m-05** `allow_same_mapping_epoch`（same-epoch continuation）生产无调用者（仅 `draft_window_async.py:149` 自身）→ async spec 中的“same-epoch continuation”目前是 **host-only** 能力，应标注为 Report1/host 契约，避免被读成生产已启用（LOCAL_FIX，文档）。
- **m-06** `runtime_context.dsa_context_parallel` 取自 **raw** `additional_config["enable_dsa_cp"]`（`draft_window.py` 的 `build_draft_window_runtime_context`），而真实 builder 选择用**已验证**的 `AscendConfig.enable_dsa_cp`（`ascend_config.py:664` 会再收窄为 `has_indexer ∧ use_sequence_parallel_moe`）。方向是安全的（raw=True/effective=False → CP builder 不存在 → UNRESOLVED → REPORT1 ✓），但两个事实源可分歧 → 建议统一读取 `get_ascend_config().enable_dsa_cp` 或显式说明（LOCAL_FIX）。
- **m-07** “resident set” 术语：`valid_num_blocks` 是 canonical CPU owner 的**已分配** block 计数，不是物理驻留探针；对已放行 route 二者相等，因为唯一非驻留机制（`sparse_kv_offload_config`）只服务 SFA 且 SFA 为 REPORT1。→ 文档应写出这一依赖（LOCAL_FIX，文档），我已在 §8 提供源码依据。
- **m-08/m-09/m-10**（§28 缺失假设行）TP×async、prefix×async、ordinary-TP×DSA 三个组合缺少 Register 行 → 增补（REPORT1）。

## Question

- **Q-01** window **OFF** 的 plain DSA-CP 是否进入 owner 要求的证据范围？（决定 M-01 的 NPU 用例是必做还是可选）
- **Q-02** 是否要求把 `W` 与 `num_speculative_tokens` 升为 topology fingerprint/identity 的**显式字段**，以便 NPU artifact 直接按 W/K 归因？（当前只能通过 descriptor fingerprint 间接归因）
- **Q-03** async 容量策略：固定容量硬错误、还是有界等待/同步回退？（M-02 的 owner 决策）

---

# 19 Capability Matrix Corrections

| 矩阵行 | 我的核验 | 需要的修正 |
|---|---|---|
| Eagle3 static-K / DFlash / eligible DSpark = `LOCAL_STATIC_READY` | 三者在 production 均有 consumer：capability 入口、proposal epoch、phase plan、逐行描述符、AR/DFlash 元数据构建、generation identity ✓ | 无 |
| uncompressed DSA / DSA-CP = `LOCAL_STATIC_READY` | provider kind + ratio 门 + 真实 builder 均已验证 ✓ | 无（**但**建议加一行说明共享 `attn_utils` 变更，见 M-01） |
| compressed DSA = `SOURCE_BLOCKED` | 由真实 builder 的 `compressor_ratio` 判定，且早于 allocation ✓ | 无 |
| SFA / MLA / native-recycling / unknown = `REPORT1_RUNTIME_DEPENDENT` | `UNRESOLVED` 分支先于 allocation ✓ | 无 |
| ordinary TP2/4/16 = `LOCAL_STATIC_READY` | rank 来源真实、无 rank0 兜底、无 world-size 除法 ✓ | 无 |
| async DFlash/DSpark = `LOCAL_STATIC_READY` | 池生产化 + 事件适配 + metadata 生命周期 ✓ | **加注**：默认 lane 数 2 与耗尽即错（M-02/m-04） |
| async Eagle3 / async DSA = `REPORT1_RUNTIME_DEPENDENT` | gate 在 allocation 前拦截 ✓ | 无 |
| prefix（含 eviction/reuse）= `LOCAL_STATIC_READY` | source/映射/请求身份不匹配即拒 ✓ | **加注**：`resident` 术语依赖（m-07） |
| terminal / mixed / batch>1 / reorder / finish-add / row reuse / preempt = `LOCAL_STATIC_READY` | 逐行描述符 + row-phase identity + epoch 校验 ✓ | 无 |
| Graph = `GRAPH_FROZEN`、COMPATIBILITY = `SOURCE_BLOCKED` | 均在最前拒绝 ✓ | 无 |
| （P7 旧矩阵）`READY_FOR_NPU` / `prefix→FAIL_CLOSED` | 已被 P7-X 取代且 gate 函数已成死代码 | 标注 superseded（m-02） |

**UNJUSTIFIED_READY / OVERCLAIMED_ROUTE / MISSING_GATE：未发现**（除上述加注项）。

---

# 20 Final Verdict

## 20.1 Mandatory Resolution Table

| ID | Severity | Area | Reviewer verdict | Needs local fix? | Needs Report1? | Needs NPU? | Release impact |
|---|---|---|---|---|---|---|---|
| M-01 | Major | attn_utils 共享路径（DSA-CP） | 改动正确且必要，但需在交付物单列并补 window-OFF 证据 | No（文档/矩阵） | Yes | Yes | 影响 DSA-CP release scope |
| M-02 | Major | async 容量与压力语义 | 策略未定；默认容量 2 且耗尽即 EngineCore 级报错 | Yes（文档/口径，可选降级） | Yes | Yes | async release 门 |
| m-01 | Minor | 拓扑指纹文档 | spec 过度描述字段集 | Yes（文档） | No | No | 审计可读性 |
| m-02 | Minor | 死 Gate / 矩阵权威 | P7 gate 生产死代码；旧矩阵仍标 canonical-live | Yes（文档/清理） | No | No | 审计正确性 |
| m-03 | Minor | resident snapshot API | `validate_expected` 生产未调用 | Yes | No | No | 无 |
| m-04 | Minor | 配置键文档 | `draft_window_async_lanes` 未文档化 | Yes（文档） | No | No | 运维可用性 |
| m-05 | Minor | same-epoch continuation | 生产不可达，应标 host-only | Yes（文档） | No | No | 无 |
| m-06 | Minor | DSA-CP 配置事实源 | raw vs validated 可分歧（方向安全） | Yes | Yes | No | 无（保守） |
| m-07 | Minor | resident 术语 | 已分配 ≠ 物理驻留（当前 route 等价） | Yes（文档） | Yes | No | 无（有依赖说明） |
| m-08 | Minor | Register 缺 TP×async 行 | 组合假设未登记 | No | Yes | Yes | async×TP16 scope |
| m-09 | Minor | Register 缺 prefix×async 行 | 组合假设未登记 | No | Yes | Yes | prefix×async scope |
| m-10 | Minor | Register 缺 TP×DSA 行 | 组合假设未登记 | No | Yes | Yes | DSA×TP scope |
| Q-01..03 | Question | scope/字段/容量策略 | 需 owner 决策 | — | — | — | 见各条 |

## 20.2 Route-by-route Verdict

```text
TP16:                        APPROVE_STATIC      （replicated 语义 SOURCE_PROVEN；NPU per-rank operand 待验）
DSA-CP:                      APPROVE_STATIC      （真实 builder + ratio 门；见 M-01 的 window-OFF 证据口径）
ASYNC DFLASH/DSPARK:         APPROVE_STATIC      （状态机/生命周期 SOURCE_PROVEN+CPU_STATIC_TESTED；NPU event ordering 与容量策略待验 → M-02）
ASYNC EAGLE3:                REPORT1_DEPENDENT   （gate 在 allocation 前拦截，未误开）
ASYNC DSA/DSA-CP:            REPORT1_DEPENDENT   （同上；lane-owned derived buffers 未建立）
PREFIX:                      APPROVE_STATIC      （canonical source + persistent valid counts；eviction/reuse 物理行为待验）
CHUNKED PREFILL:             APPROVE_STATIC      （三态分类与 pinned 计数语义一致，含 pre-step 时序核验）
MIXED:                       APPROVE_STATIC      （逐行 full/window；无条件 NotImplementedError 已消除；后端 batch-global 假设待验）
MULTI-REQUEST:               APPROVE_STATIC      （epoch/请求指纹/行相位/拓扑/lane 全部进入 identity）
DENSE GQA:                   APPROVE_STATIC
UNCOMPRESSED DSA:            APPROVE_STATIC
COMPRESSED DSA:              SOURCE_BLOCKED      （正确拒绝，allocation 前）
SFA:                         REPORT1_DEPENDENT
MLA:                         REPORT1_DEPENDENT
HOMOGENEOUS MULTI-GROUP:     REPORT1_DEPENDENT   （live 单组约束仍在；无 fake PASS）
HETEROGENEOUS MULTI-GROUP:   REPORT1_DEPENDENT   （未复制 MRV1 repeated-window 缺陷）
```

（`APPROVE_STATIC` ≠ `SUPPORTED`；本地静态契约通过不等于 NPU 支持。）

## 20.3 Mandatory Global Verdict

```text
P7-X REVIEW:
APPROVE WITH REQUIRED FIXES
   Required（均非 production 代码改动）：
     1) M-01：交付物单列 attn_utils 共享路径变更 + NPU 矩阵补 window-OFF DSA-CP 用例 + Register 加行
     2) M-02：owner 明确 async 容量/耗尽策略，并保留 ASYNC-PRESSURE 为必做 NPU 用例
     3) m-01/m-02/m-04/m-05/m-07：文档口径修正（指纹字段、旧矩阵 superseded、lane 配置键、host-only 标注、resident 依赖说明）
     4) m-08/m-09/m-10：Register 增补三条组合假设行

P7-X PRODUCTION WIRING:      FACTUAL
CAPABILITY MATRIX:           NEEDS CORRECTION（仅口径/加注；状态值无过度声明）
TP16 STATIC CONTRACT:        PASS
DSA-CP STATIC CONTRACT:      PASS
ASYNC STATIC/LIVE BINDING:   PASS（NPU event ordering + 容量策略 = REPORT1/owner）
PREFIX STATIC CONTRACT:      PASS
CHUNKED/MIXED STATIC CONTRACT: PASS
MULTI-REQUEST STATIC CONTRACT: PASS
TARGET/WRITE INVARIANTS:     PASS
FORCED-OFF POLICY:           PASS
GRAPH FREEZE:                PRESERVED
vLLM:                        UNCHANGED
MRV1:                        UNCHANGED
REPORT1 ASSUMPTION REGISTER: NEEDS ADDITIONS（m-08/m-09/m-10）
READY FOR CODEX ADJUDICATION: YES

EAGER NPU VERIFIED:          NO（本轮未运行 NPU，未登录 Node101）
```

## 20.4 Evidence-level summary（§29）

| 事项 | 级别 |
|---|---|
| TP replicated 读视图、rank 来源、无 V/world_size | SOURCE_PROVEN |
| phase 三态分类与其 pre-step 时序 | SOURCE_PROVEN |
| 逐行 full/window 描述符、full-width workspace 容量校验 | SOURCE_PROVEN |
| forced-OFF / CONFIG_OFF / Graph / COMPATIBILITY 前置拒绝 | SOURCE_PROVEN |
| async 状态机（abort 分支、重试、lane 独立性、metadata 保留） | CPU_STATIC_TESTED（我执行探针 + 新测试） |
| DSA-CP 共享 kwargs 修复 | CPU_STATIC_TESTED（父 red / P7-X green，§16.2） |
| 六个 workstream 的 host 契约与 291/608 等测试数字 | CPU_STATIC_TESTED（我复现） |
| TP16 实际 per-rank operand / slot / 输出 | NPU_REQUIRED |
| DSA/DSA-CP local derived metadata、物理读集、通信 | NPU_REQUIRED |
| async event 可见性、stream happens-before、容量上界 | NPU_REQUIRED |
| prefix 命中/共享/驱逐/复用、mixed batch 真机行为 | REPORT1_REQUIRED / NPU_REQUIRED |
| GLM/Qwen 实际 model/backend/gid/ratio/topology 组合 | REPORT1_REQUIRED |

---

## 附录 A — 我的复现命令

```bash
cd /Users/wenqingzhang/Desktop/vllm/vllm-ascend
git rev-parse HEAD HEAD^{tree}; git status --porcelain -uall
git diff --shortstat 4753742..7e88db6
git diff --name-only 4753742..7e88db6 | grep -iE "graph|aclgraph|cudagraph"

run() { env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q "$@"; }
run tests/ut/spec_decode/test_draft_window.py tests/ut/spec_decode/test_draft_window_nongraph.py \
    tests/ut/spec_decode/test_draft_window_async.py tests/ut/spec_decode/test_draft_window_eager.py \
    tests/ut/spec_decode/test_draft_window_eagle3.py tests/ut/worker/test_attn_utils_v2.py   # 291 passed
run tests/ut/spec_decode/                       # 608 passed, 13 skipped, 7 failed(env)
run tests/ut/attention/                         # 472 passed
run tests/ut/_310p/                             # 155 passed
run tests/ut/worker/v2/ tests/ut/worker/test_block_table.py tests/ut/worker/test_attn_utils_v2.py \
    tests/ut/worker/test_dcp_manager.py tests/ut/worker/test_pcp_manager_v2.py               # 147 passed
run tests/ut/test_compressed_prefix_cache.py tests/ut/patch/platform/test_prefix_cache_cp_patches.py \
    tests/ut/models/test_glm5next_kv_cache.py tests/ut/models/test_glm5next_cache_config.py  # 74 passed

# 静态
.venv/bin/python -m ruff check <5 生产文件>; .venv/bin/python -m ruff format --check <13 文件>
.venv/bin/python -m compileall -q vllm_ascend/worker/v2/spec_decode/ vllm_ascend/worker/v2/attn_utils.py
git diff --check 4753742..7e88db6

# parent-red（temp worktree，只放入 P7-X 版测试；生产保持父版本）
git worktree add -q --detach /tmp/p7x-parent 4753742
cd /tmp/p7x-parent && git checkout 7e88db6 -- tests/ut/worker/test_attn_utils_v2.py tests/ut/spec_decode/test_draft_window*.py
env VLLM_VERSION=0.29.0 PYTHONPATH=/tmp/p7x-parent:/Users/wenqingzhang/Desktop/vllm/vllm \
  <repo>/.venv/bin/python -m pytest -q tests/ut/worker/test_attn_utils_v2.py   # 1 failed: KeyError 'common_ratio_to_sas_metadata'
cd <repo> && git worktree remove --force /tmp/p7x-parent
```

自建探针（`/tmp`，未写入仓库）：
- `/tmp/p7probe/p8_probe2.py` 系（async 状态机/拓扑漂移/alias，P7 轮建立，本轮复用同类构造）
- 本轮新增：lane 独立 backing / pressure / abort-after-submit 的行为复核（复用 UT helper，未落盘到仓库）

（本轮未执行：Mypy、`tests/ut/core`、`tests/ut/worker` 全量、任何 NPU 步骤。）
