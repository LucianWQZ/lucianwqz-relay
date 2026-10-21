# MRV2 Draft Window P6 — DeepSeek Independent Review

> Independent reviewer（非 P6 实现者）。所有结论来自真实 source / commit / 本地测试执行；
> 未采信 Codex Notes、commit message 或测试总结。
> 日期：2026-10-13（Asia/Shanghai）。未修改任何 production 代码。

## 0. Baseline 与可复现事实

| 项 | 独立核实 |
|---|---|
| vLLM 路径 | `/Users/wenqingzhang/Desktop/vllm/vllm` |
| vLLM HEAD | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` ✔ |
| vLLM `git status --porcelain` | 空（clean / zero diff） ✔ |
| P6 parent | `0702c89d2aa41d47ae2379fc6de883140277fbef`（tree `2b8fecda15ca57c0062bbfe5eec62ecd0a4c99ac`） ✔ 与要求一致 |
| P6 commit | `20673a1ced10160d8f8d1aaa79230e6ce0409d3c`（tree `153458a4fbb21e8284ceb6b5290b10295a6b877d`） |
| P6 branch | `feature/p6-graph-read-carrier` |
| `git diff 0702c89 20673a1 --stat` | 10 files, **+2168 / −71** |
| vLLM-Ascend `git status --porcelain` | 空（clean） ✔ |

`git diff --name-only 0702c89 20673a1`（全部 vllm-ascend，**无 vLLM 路径**）：

```text
vllm_ascend/worker/v2/spec_decode/draft_window_graph.py              (+963)
vllm_ascend/worker/v2/spec_decode/draft_window.py                    (+28/−?)
vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py       (+15)
vllm_ascend/worker/v2/spec_decode/dflash/speculator.py               (+11)
vllm_ascend/worker/v2/spec_decode/dspark/speculator.py               (+11)
vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py         (+35/−?)
vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py                 (+38/−?)
vllm_ascend/compilation/acl_graph.py                                 (+19)
tests/ut/spec_decode/test_draft_window_graph_carrier.py              (new, 1043)
tests/ut/spec_decode/test_draft_window_graph_binding.py              (+76/−?)
```

## 1. Repository Boundary（§14）

| 检查 | 结果 | 证据 |
|---|---|---|
| vLLM 是否变化 | **无** | HEAD 与要求一致、clean；diff 列表无 vLLM 路径 |
| private patch / site-packages | **无** | `grep -n "site-packages\|sys.path\|importlib" draft_window_graph.py` → none |
| module global / ContextVar | **无** | 模块内无 module-level 赋值语句；无 `ContextVar`/`contextvars`；provider 是 **instance attribute** `_draft_window_graph_binding_provider` |
| runtime monkeypatch | **无新增** | P6 复用既有 `build_attn_metadata_wrapper()`；未新增 import-time rebind |
| shared owner swap | **无** | 无 `block_tables.input_block_tables =` / `input_buffers.seq_lens =`；carrier 是 `zeros_like(...)` 新建 storage（测试断言 `owner_id != id(workspace)`、`storage_data_ptr != canonical`） |
| Target 写入 | **无** | P6 模块内无 `model_state` / `attn_metadata` 引用；Target 隔离改由共享 oracle 强制 |

## 2. §3 — M-01 是否真的关闭（逐箭头追踪）

真实数据流（我按 source 逐点核对）：

| 箭头 | code 位置 | data | owner | generation |
|---|---|---|---|---|
| Window/P3 source | `draft_window.py` P3 workspace + `DraftMetadataInputs` | 5 个 window tensor | speculator（P3） | P3 generation + mapping_epoch |
| P6 carrier | `draft_window_graph.py::bind_read_carrier:608-703` | `destination.copy_(source)` 到 `_DraftWindowGraphCarrierBacking` | **provider（instance）** | runtime identity 由 P3 generation 投影（`_make_binding_identity`） |
| `build_draft_attn_metadatas` | `autoregressive/speculator.py:777-790`；`dflash/speculator.py:69-78`；`dspark/speculator.py:157-166` | `consume_draft_window_graph_metadata(...)` 返回值 | speculator | 携带 carrier metadata 对象 |
| Draft metadata | `draft_window_graph.py::consume_metadata:705-765` | `carrier.metadata`（对象 identity） | 独立构建 + P3 store | 同一 generation |
| `update_full_graph_params` | `compilation/acl_graph.py:318-334` | 同一 metadata 对象 | Ascend graph helper | — |
| backend update | `acl_graph.py:335+` → `impl_cls.update_graph_params(...)` | — | `AscendAttentionBackendImpl`（精确类） | attribution 在此派生 |
| actual graph consumer | 未观测（NPU） | — | — | `NEEDS_NPU_TIMELINE` |

逐项回答：

- **有没有 baseline fallback？** **没有。** `consume_metadata` 在 carrier 数量/ordinal/proposal/epoch/request-fingerprint/gid 任一不符时 `RuntimeError`（`:727-751`），**不返回 None**；`consume_draft_window_graph_metadata` 仅在 **provider 完全不存在** 时返回 `None`（`:1332-1334`）。测试 `test_provider_exists_without_explicit_carrier_fails_before_baseline_metadata_can_win:367-384` 用 "provider 存在 + 无 carrier" 断言 `consume` 与 `assert_metadata_batch` 双双抛错。
- **是否可能静默使用 Target-derived metadata？** **不能。** `assert_metadata_batch:767-788` 用 `id()` 逐个比较 metadata 对象与已提交 carrier，不符即 `RuntimeError("baseline or Target-derived metadata cannot replace the explicit graph read carrier")`；该断言在 **replay 之前**（两个 manager 的 `run_fullgraph` 内、`super().run_fullgraph()` 之前）执行；`validate_backend_update:823` 在 UPDATE 入口再次比对同一批 `id()`。
- **carrier 是否真的被 metadata 消费？** `_validate_metadata_uses_carrier:1012-1041` 要求每个 layer metadata 的 `block_tables`/`seq_lens`/`seq_lens_cpu` 的 **storage_data_ptr** 等于 carrier 对应 tensor，且 `seq_lens_list` 前缀等于 carrier CPU exact。

**结论：P5 的 M-01 在 replay/update 侧静态关闭 ✓。** 生产入口（3 个 speculator 的 `build_draft_attn_metadatas`）+ replay 前断言 + UPDATE 入口断言三层齐全，且 provider 缺失时严格 baseline。

## 3. §4 CaptureIdentity（Q-01）

`DraftWindowGraphCaptureIdentity:218-226` 只含 `fingerprint / execution_lane / consumer_ordinal / provider_schema_version / backing_identity`；`DraftWindowGraphBindingIdentity:268-286` 才含 generation_id / mapping_epoch / request fingerprint / phase / step。**两个 namespace 物理分离** ✓；`bind_read_carrier` 对非 CaptureIdentity 直接 `TypeError`（`:618-619`）✓；无 `generation_id=0`、无伪造 request id、无伪造 epoch ✓（测试 `test_capture_identity_is_not_a_runtime_generation_namespace:301`、`test_fake_caller_consumer_declaration_cannot_override_backend_fact:604-610` 断言 `consumer_kind` 不是 CaptureIdentity 字段）。

兼容关系显式：`_validate_runtime_capture_compatibility:971-985` 比对 method / gid / padded_request_count / lane；`_validate_route:455-469` 比对 route↔method↔phase↔step；fingerprint 其余 26 字段在注册时与 **P2 inventory** 交叉校验（`register_capture_identity:547-570`）✓。**capture 不依赖 active proposal** ✓（`register_capture_identity` 不需要 epoch/lease）✓ — Q-01 的结构诉求已满足。

## 4. §5 Capture Dummy Metadata

- `observe_draft_window_graph_capture:1307-1322`：**provider 存在时无条件 `RuntimeError`**（"P6 has no safe Ascend-only capture carrier seam in the pinned vLLM"）；provider 不存在时 exact no-op ✓。
- 测试 `test_startup_capture_with_runtime_provider_fails_instead_of_faking_generation:667-673` ✓。
- 我核对了上游路径：dummy metadata 由 `cudagraph_utils.prepare_inputs_to_capture` / `dflash/cudagraph.py::_prepare_dflash_inputs_to_capture` **内部**用 `get_dummy_block_tables()` 创建，签名无 provider/sink 参数；Ascend 的 `…AclGraphManager.capture()` 虽然包住 `super().capture(...)`，但 dummy metadata 在 upstream helper 内部生成，**没有可注入的 Ascend-owned 入口**。

**因此 capture 侧不是 "OBSERVATION_ONLY"，而是明确拒绝 = BLOCKED**（这是诚实处理，不是伪完成）✓。P6 没有把 "observe CAPTURE" 写成 "capture carrier PASS"（Notes §11/§19 亦写 `CAPTURE PATH: BLOCKED`）✓。

## 5. §6 Replay / Update Timeline 与 one-step lag

我重新从 source 确认顺序（未偷换）：

```text
build_draft_attn_metadatas（含 P6 consume）
-> assert_draft_window_graph_metadata_batch（replay 前）
-> update_stream.wait_stream
-> observe(REPLAY)
-> super().run_fullgraph(desc)            # REPLAY
-> observe(CONSUMER)
-> build_draft_window_graph_update_binding
-> observe(UPDATE) / validate attribution
-> update_full_graph_params -> impl_cls.update_graph_params
```

证据：`autoregressive/aclgraph.py:171`（assert）、`:181`（REPLAY observe 在 `super().run_fullgraph` 之前，见 diff）、`:218`（binding）、`update_full_graph_params` 在其后；`dflash/aclgraph.py:117/127/152`。**没有** 被改成 `UPDATE → REPLAY` ✓。

one-step lag：`DraftWindowGraphReplayUpdateTimeline.update_effective_generation_ids = None`、`consumer_generation_ids = None`（`:756-763`、`:881-888`），`status` 恒为 `NEEDS_NPU_TIMELINE`（`:83-86`），`assert_update_effective_for:904-906` **无条件抛错**（"effective graph update generation requires NPU timeline evidence"）✓。测试 `test_replay_update_timeline_refuses_to_claim_same_or_next_generation:613-664` 断言两个字段为 `None` 且该 API 抛错 ✓。

**没有把 update(N) 写成影响 N 或 N+1** ✓ — 该问题被显式保持 OPEN。

## 6. §7 Backend Attribution

`update_full_graph_params(..., draft_window_graph_update_binding=...)`（`compilation/acl_graph.py:312,320-334`）在 `set_current_vllm_config` scope 内先 `attn_backend.get_impl_cls()` / `get_builder_cls()`，再调用 `validate_draft_window_graph_backend_update(...)` **紧接其后**才 `impl_cls.update_graph_params(...)` ✓。

`validate_backend_update:808-890`：
- `impl_cls is not AscendAttentionBackendImpl` → 抛错（**精确类，无子类继承**）✓；
- `update_function_path` 必须等于 `"vllm_ascend.compilation.acl_graph.update_full_graph_params"` ✓；
- 真实 `backend_impl`/`builder_impl` 必须等于每个 carrier fingerprint 的值 ✓；
- metadata 的 layer key 必须是 P2 inventory layer group 的子集（Target-only layer 会 fail）✓；
- 逐 carrier 重新 `_validate_metadata_uses_carrier` ✓；
- 只有通过后才以 `backend_class / backend_impl / builder_impl / update_function_path / gid / layer_group` 构造 `DraftWindowGraphBackendAttribution(consumer_kind=TASK_REBOUND)` ✓。

测试：`test_backend_attribution_is_derived_from_actual_update_path:497-543`、`test_actual_update_entry_resolves_backend_before_attribution:546-601`（调用**真实** `update_full_graph_params`，仅 monkeypatch `AscendAttentionBackendImpl.update_graph_params`，断言 backend 方法被调用 1 次且 attribution 已派生）✓、`test_fake_caller_consumer_declaration_cannot_override_backend_fact:604-610`（attribution dataclass 缺字段即 `TypeError`）✓。

**P5 的 m-02 关闭 ✓**：`consumer_kind` 不再是 caller 可声明的证据（P5 遗留 `bind()` API 的 caller 声明仅用于 expected-binding 观测，其 docstring 已改为 "not an operator-consumption attestation"，且 P6 的 attribution 路径不经过它）。

## 7. §8 Consumer Matrix 抽查（不得靠继承自动成立）

| Cell | 代码事实 | 我的判定 |
|---|---|---|
| Eagle3 first-pass / FULL | AR `build_draft_attn_metadatas(is_draft_model_prefill=True)` → `expected_consumer_count=1`（`:783`） | 与 matrix "PARTIAL（carrier 契约证明、capture 阻塞）" 一致 |
| Eagle3 AR / FULL | `expected_consumer_count = len(input_buffers.draft_seq_lens_cpus)`（`:783`）；该 list 由 `num_speculative_steps - 1` 构造（`speculator.py:156-160`，仅 `decode_mode()==FULL` 时存在）→ K=3 时 2 个消费点 | **不是 first-consumer-only** ✓；计数来源为真实 buffer 列表而非常量 ✓ |
| DFlash / FULL | `AscendDFlashSpeculator.build_draft_attn_metadatas`（`:69`）route=DFLASH，count=1 | ✓ |
| DSpark / FULL | 独立 override（`:157`）route=DSPARK；manager 侧由 `_speculator_name.lower()=="dspark"` 选择 route（`dflash/aclgraph.py:104-108`） | ✓（DFlash/DSpark method 未混用：`_validate_route` 会因 method≠"dflash"/"dspark" 抛错） |
| FULL_DECODE_ONLY / PIECEWISE（全部 route） | 无 provider 时 baseline；有 provider 时 P2 的 `graph_mode != "NONE"` gate 已在更早阶段拒绝，matrix 标 `BLOCKED`/`UNRESOLVED` | ✓ 与代码一致 |
| `DIRECT_CAPTURED` / `BACKEND_DERIVED` | 代码中**无任何 route** 派生这两类（只有 `AscendAttentionBackendImpl` 精确类 → `TASK_REBOUND`） | ✓ 与 matrix "No route classified" 一致 |
| Target consumer 被当 Draft consumer | metadata layer key 必须 ⊆ P2 inventory layer group（`validate_backend_update:853-858`） | ✓ 有显式防线 |

`P6_Graph_Consumer_Matrix.md` 的每一格都是 `PARTIAL / BLOCKED / UNRESOLVED`，**没有**任何 "supported/enabled" 声明 ✓；且未用共享基类推导支持面 ✓（Eagle3/DFlash/DSpark 分行，DFlash_DECODE_ONLY 与 PIECEWISE 独立列 `BLOCKED`）。

## 8. §9 Draft-private Metadata / Target Isolation

- `bind_read_carrier` 强制 `validate_draft_metadata_isolation(metadata, target_metadata=...)`（`:672-675`），该 oracle 由 P3 store 提取为共享函数（`draft_window.py:2262-2276`），覆盖 nested object / Tensor storage / NumPy shared memory ✓；
- `DraftWindowGraphReadInputs` **不含** positions / slot_mapping / Target / canonical owner ✓（`:229-240`）；
- 测试 `test_explicit_carrier_builds_draft_private_metadata_and_preserves_target:424-477`：Target root/layer identity 不变，`block_tables`/`seq_lens`/`slot_mapping`/`positions`/`query_start_loc`/nested Tensor/nested numpy 全部内容不变，canonical table 不变 ✓；`test_carrier_rejects_nested_target_aliases:479-494` 断言 alias 被拒 ✓；
- P6 模块内无对 `model_state.attn_metadata` 的任何写入 ✓。

**未发现任何 Target / canonical / slot / positions / query 污染。**

## 9. §10 Route Fingerprint

`DraftWindowGraphRouteFingerprint:114-215` 含 26 字段（method/route/graph_mode/backend_impl/builder_impl/gid/layout/capture_descriptor/capture_bucket/query_width/padded req+token/static_k/W/logical+kernel block size/block span/TP/DP/PP/PCP/DCP/SP/DSA-CP/FlashComm/async/prefix）。

**真实影响 validation**（不是仅存在字段）：
- `__post_init__` 逐项强校验（route↔method、mode ∈ {FULL, FULL_DECODE_ONLY, PIECEWISE}、bucket == padded geometry、query width ↔ padded tokens、K/W/block geometry > 0、bool 不能冒充 int）；
- **单 lane 拓扑硬拒绝**：TP/DP/PP/PCP/DCP>1、SP、DSA-CP、FlashComm、async、prefix cache 任一为真 → `ValueError`（`:202-215`）✓；
- 实例化时按 `_ROUTE_CONTRACTS` 推断 phase/step 约束 ✓；
- 注册时与 P2 inventory 交叉校验 ✓；UPDATE 入口与真实 backend/builder 交叉校验 ✓。

负例测试：`test_capture_route_fingerprint_mismatch_fails_closed:333`（参数化逐字段改动）、`test_capture_query_width_must_match_padded_token_geometry:362` ✓。

## 10. §11 Eagle3 Per-step

`test_eagle3_k3_carriers_keep_distinct_step_sources_and_frozen_proposal:736-818`：3 个 carrier（ordinal 0/1/2），3 个连续 generation（`materialize` + `materialize_serialized_step`），E = 65/66/67，source start = 0/1/2；断言三轮 metadata 的 `seq_lens_list[0]` 分别为 65/66/67 ✓、step 序列 [1,2,3] ✓、**同一 mapping_epoch** ✓、**三个 backing 地址互不相同**（`len({storage_data_ptr}) == 3`）✓。`consume_metadata` 另行强制三个 carrier 同 proposal / 同 epoch / 同 request fingerprint / 同 gid（`:739-748`）✓。

未发现 table lag 一 step / length lag 一 step / 以旧 Window 为 source（每 step 从 P3 materialization 复制 ✓，且 P4b 的 `describe_frozen_step` 保证 S 冻结、E 变化 ✓）。`use_fused_multi_step_decode = False` 仍在（P4b 设定）✓，避免 "build once, mutate per step"。

## 11. §12 A/B/A 证据等级

Notes 与 `P6_Replay_Update_Timeline.md` 把该证据严格命名为 **`P6 HOST A/B/A`**，并写明 `P6 NPU A/B/A: NOT VERIFIED`；`test_host_a_b_a_has_stable_backing_distinct_generations_and_no_stale_reuse:676` 断言地址稳定、内容不同、A′ 语义相同但 generation 不同、stale A 被拒。**没有**把 host A/B/A 写成 Graph correctness ✓（与 P5 的 Q-02 诉求一致）。

## 12. §13 Graph User Gate

- `draft_window.py:880` 的 `graph_mode != "NONE"` 拒绝仍然存在，且 P6 **未改动**该行（`git diff 0702c89 20673a1 -- draft_window.py` 只提取了 isolation oracle）✓；
- `install_draft_window_graph_binding_provider` **无 production caller**（我逐一 grep：`install_*` / `register_capture_identity` / `bind_read_carrier` 在 `vllm_ascend/` 内的非本模块引用数 = **0**）✓ → 4 个生产 wrapper 全部 no-op → 生产行为零变化 ✓；
- 因此 `FULL / FULL_DECODE_ONLY / PIECEWISE` 的 Window ON 仍 fail closed ✓，NPU 证据为零却未开放用户 Gate ✓。

## 13. §15 独立测试执行（不复制 Codex 数字）

环境：`VLLM_VERSION=0.29.0`，`PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm`（未修改的原版 checkout），`.venv/bin/python -m pytest -q`。

| Scope | 我的结果 | 与 Notes 对比 |
|---|---|---|
| P6 targeted `test_draft_window_graph_carrier.py` | **23 passed** | 一致 ✓ |
| P5 targeted `test_draft_window_graph_binding.py` | **37 passed** | （Notes 的 60 = 23+37）一致 ✓ |
| P5+P6 graph targeted | **60 passed** | **一致 ✓** |
| full `tests/ut/spec_decode` | **532 passed, 13 skipped, 7 failed, 2 subtests** | **一致 ✓** |
| P1–P6 + attn/attn_utils/block_table（我构造的 9 文件） | 392 passed | — |
| 上列 + DFlash2/DSpark/extract（13 文件） | **436 passed** | Notes §16 的 `423 passed, 23 subtests` **未能逐项复现**（清单未给出）；见 m-04 |
| `ruff check`（10 个改动文件） | **All checks passed** | 一致 ✓ |
| `ruff format --check` | **already formatted** | 一致 ✓ |
| `compileall` | **OK** | 一致 ✓ |
| `git diff --check` | **OK** | 一致 ✓ |
| `mypy --follow-imports skip`（P6 模块） | **Success: no issues found** | 一致 ✓ |
| actionlint / gitleaks / NPU | **NOT RUN** | 本机不可用（Notes 亦记 environment-blocked；我不改写成 PASS） |

**VWN 7 项失败重新分类（未按历史自动忽略）**：我重跑单项并读栈，失败为 `vllm/v1/attention/selector.py:208 ValueError: Invalid attention backend for None`，且失败运行的输出中 **对 P6 文件引用为 0**（`grep -c draft_window_graph` = 0）；属本机无 Ascend backend 的 host 平台问题，与 P6 数据面无关。**不作为 PASS，也不当作 P6 regression。**

## 14. Findings

### Q-01 — capture carrier 注入路径在当前 repository boundary 下不可实现 ⇒ Graph enablement 被 architecture/repository blocker 阻塞

- **ID**: Q-01  **Severity**: **Question / Architecture-Repository blocker（非代码缺陷）**
- **Claim**: P6 声称建立 "Graph read carrier"（Notes §19 `P6 GRAPH READ CARRIER: PASS`）。
- **Exact source**:
  - `draft_window_graph.py:1307-1322`（`observe_draft_window_graph_capture` 在 provider 存在时无条件抛错）；
  - 上游 dummy metadata 生成点：`vllm/v1/worker/gpu/cudagraph_utils.py:678-735`（`get_dummy_block_tables()` + `model_state.prepare_attn(...)`）、`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24-63`（`_prepare_dflash_inputs_to_capture` 内部自建 dummy 表，签名无 provider/sink 参数）；
  - Ascend 侧可覆盖的最外层是 `…AclGraphManager.capture()`（`autoregressive/aclgraph.py:93`、`dflash/aclgraph.py:77`），但 dummy metadata 在其 `super().capture(...)` 内部生成。
- **Observed behaviour**: capture 恒被拒绝；`P6 CAPTURE PATH = BLOCKED`。read carrier 只在 **replay/update** 侧成立（P6 的 consume/assert/attribution 全在 replay 及其后）。
- **Expected contract**: Final Design 要求 Window ON 的 graph 路径在 capture、live、replay 三个入口都使用同一 read contract（capture entry 不可缺失）。
- **Why it matters**: 一个"捕获时不被绑定的 read carrier"无法让 captured graph 读取窗口 read plane。因此 P6 无法把 Graph Window 推进到 enablement；这是整个 feature 的 Graph 分支能否成立的前置问题，需要 owner 决策而非实现者绕过。
- **Reproduction**:
  ```bash
  sed -n '1307,1322p' vllm_ascend/worker/v2/spec_decode/draft_window_graph.py
  grep -n "get_dummy_block_tables\|dummy" /Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py
  env VLLM_VERSION=0.29.0 PYTHONPATH=... .venv/bin/python -m pytest -q \
      tests/ut/spec_decode/test_draft_window_graph_carrier.py -k startup_capture
  ```
- **Required correction**: owner 必须在下列三选一中裁决（P6 Notes §11 已如实列出，我确认三条都成立）：
  1. 找到一个**已存在但尚未发现**的 Ascend-owned pre-capture operand 注入点（我未发现；需要 owner/backend 团队确认）；
  2. 批准 **vendor-local 最小 capture assembly**（复制 upstream capture helper 的 metadata 组装部分）并接受其 drift 成本与相应 AST guard；
  3. 修改 vLLM 增加 vendor-neutral capture hook（**当前 R-REPO-01 禁止**）。
  在该裁决完成前，不得宣称 Graph 分支可交付。
- **Architecture escalation needed?** **是（明确需要）**。

### m-01 — carrier metadata 的 write-side parity（slot/positions/query/attn_state）未被校验

- **ID**: m-01  **Severity**: **Minor**
- **Claim**: P6 §9 Notes 称 builder 输出必须满足多项契约；Notes §17 断言 "full slot mapping untouched / positions-query layout untouched"。
- **Exact source**: `draft_window_graph.py::_validate_metadata_uses_carrier:1012-1041` — 只校验 `block_tables` / `seq_lens` / `seq_lens_cpu` 的 storage 与 `seq_lens_list` 的值。
- **Observed behaviour**: 未校验 metadata 的 `slot_mapping` / `positions` / `query_start_loc` / `attn_state` 是否等于 canonical/baseline 来源。P4a/P4b eager 路径有这些约束（`slot_mappings=self.block_tables.slot_mappings[...]`、positions 由 factory 注入、`attn_state` 从 Target 或 DecodeOnly 赋值），carrier 路径把 metadata 构建完全交给 caller 的 `metadata_builder`，只检查 read 侧。
- **Expected contract**: Graph Window ON 也不得改变 write-side 字段（Final Design 不变量）。
- **Why it matters**: 未来 P7 的 carrier builder 若传入 window 化的 `slot_mapping`（或残留 dummy 表），P6 的校验不会发现，而 FIA 的写入地址会随之改变 —— 这是本 feature 最高危的破坏面之一。
- **Reproduction**: 构造一个 `metadata_builder`，令其 metadata 的 `block_tables/seq_lens/seq_lens_cpu` 来自 carrier、但 `slot_mapping` 来自 `carrier.read_inputs.window_block_table`；`bind_read_carrier` 仍会成功（当前测试集无此负例）。
- **Required correction**: 在 `_validate_metadata_uses_carrier` 中增加 write-side 断言：`slot_mapping` 必须是 canonical `block_tables.slot_mappings`（storage 或内容）、`positions`/`query_start_loc` 必须等于 baseline 来源、`attn_state` 必须属于允许集合；并补一个负例测试。
- **Architecture escalation needed?** 否。

### m-02 — DFlash/DSpark route 由 `_speculator_name` 字符串推导，而非 P2 inventory method

- **ID**: m-02  **Severity**: **Minor**
- **Exact source**: `dflash/aclgraph.py:104-108`（`speculator_name.lower() == "dspark"` → DSPARK，否则 DFLASH）。
- **Observed behaviour**: route 选择依赖上游 `_speculator_name` 字符串；DFlash2（`"DFlash2"`）会落到 DFLASH 分支。当前**不可达**（DFlash2 无 P3 state → provider 无法安装），且即便误判也会被 `_validate_route`（fingerprint route↔generation method/phase/step）拒绝 ✓，因此不是可利用缺陷。
- **Required correction**: 从 P2 inventory 的 `method`（或 generation.normalized_method）推导 route，避免字符串启发；至少加一条注释说明为何在此处可接受。
- **Architecture escalation needed?** 否。

### m-03 — 安装 provider 会使引擎 startup capture 硬失败，该耦合需显式文档化

- **ID**: m-03  **Severity**: **Minor**
- **Exact source**: `draft_window_graph.py:1315-1322` + `install_draft_window_graph_binding_provider:1264-1286`。
- **Observed behaviour**: 一旦安装 provider，`capture()` 入口即 `RuntimeError`（`autoreversal/aclgraph.py:93`、`dflash/aclgraph.py:77`），而 startup capture 是每个引擎必经步骤 ⇒ **安装 provider = 引擎无法启动**。当前无 production caller，所以零影响 ✓；但 API 语义上"可安装"与"可启动"互斥。
- **Required correction**: 在 install 的 docstring/Notes 中显式写明 "installing a provider requires the capture seam to be resolved first; otherwise startup capture fails closed"，并（可选）增加一个 startup-level negative test 把该耦合固定下来，避免未来某阶段在未解决 capture 前安装 provider 造成服务不可用（与 P4a C-01/P4b C-02 同类风险）。
- **Architecture escalation needed?** 否（记录即可；但见 Q-01）。

### m-04 — Notes §16 的 `423 passed` 未给出文件清单，无法逐项复现

- **ID**: m-04  **Severity**: **Minor（文档可复现性）**
- **Exact source**: `P6_Graph_Read_Carrier_Per_Consumer_Implementation_Notes.md` §16。
- **Observed behaviour**: 我能**精确复现** `P5+P6 graph targeted = 60`、`full spec_decode = 532 passed, 13 skipped, 7 failed`；但 `P1–P6 + graph + attn/block table targeted = 423 passed, 23 subtests` 的清单未给出，我构造的最接近 13 文件组合得到 **436 passed, 2 subtests**（差 13 项、subtests 数亦不同）。
- **Required correction**: 在 Notes 中列出每条计数所包含的确切文件（P1–P6 Notes 的其它阶段已采用该做法），使第三方可复现。
- **Architecture escalation needed?** 否。

### Q-02 — manager 级测试与真实 update 入口的证据分层（说明，非缺陷）

- manager integration 测试（`test_parallel_graph_manager_carries_...:828`、`test_eagle3_graph_manager_carries_...:947`）把 `*_aclgraph_module.update_full_graph_params` 替换为 spy，因此它们证明的是 **"typed binding 被构造并传入真实 manager 调用点 + 顺序正确"**；对 **真实 `update_full_graph_params` 内部** 的后端解析与 attribution，另由 `test_actual_update_entry_resolves_backend_before_attribution:546` 直接调用真实函数证明 ✓。
- 两层合起来足以支撑 "replay/update 侧静态契约"，但**不等于**任何 NPU 结论 ✓。Notes 与 timeline 文档对此表述准确（`P6 NPU GRAPH: NOT VERIFIED`），我仅在此固定证据边界，防止后续被外推。

## 15. P5 Review 四项的处置复核

| P5 finding | 我的独立判定 | 证据 |
|---|---|---|
| **M-01**（binding 被 observe，但 graph metadata 仍来自 Target/baseline） | **CLOSED（静态）** | `build_draft_attn_metadatas` 三处优先 consume（provider 存在时缺 carrier 即抛错，不回落 baseline）；replay 前 `id()` 对象断言；UPDATE 入口再次断言；`_validate_metadata_uses_carrier` 校验 storage。测试 367/394/477 |
| **m-02**（`TASK_REBOUND` 只是 caller 声明） | **CLOSED** | attribution 在真实 `update_full_graph_params` 内由 `get_impl_cls()/get_builder_cls()` 派生，且要求精确 `AscendAttentionBackendImpl`；`consumer_kind` 不是 CaptureIdentity 字段，attribution 无法缺字段构造。测试 497/546/604 |
| **Q-01**（capture-scope identity 缺失 / capture 与 generation 混用） | **结构上已解决，capture 通路仍 BLOCKED** | `CaptureIdentity ≠ BindingIdentity`，无伪造 id/epoch，兼容关系显式；capture 注入点不存在（Q-01 本报告） |
| **Q-02**（spy ≠ operator attestation 的措辞边界） | **CLOSED（措辞已收紧）** | docstring 改为 "test ... at live/capture/replay/update/consumer boundaries ... not evidence that ... consumed that backing"（P5-final 0702c89）；`UNRESOLVED` 默认；timeline 两字段 `None`；`assert_update_effective_for` 恒抛错 |
| （P5 m-01：canonical pointer 未入 identity） | **CLOSED** | P5-final 在 `bind`/`observe` 中增加 `full_source.validate_owner_bindings()` |

## 16. 必须回答的 7 个问题

1. **M-01 Graph replay read-carrier 是否真的接通？**
   **是（静态接通）。** `build_draft_attn_metadatas` 三个生产入口 → `consume_metadata`（缺 carrier 即 hard fail，不回落 Target）→ replay 前 `id()` 断言 → `update_full_graph_params` 入口再次断言 → 真实 `AscendAttentionBackendImpl.update_graph_params`。但注意：**capture 侧未接通**（Q-01），所以整条 graph read path 尚未闭合。

2. **CaptureIdentity 是否与 runtime generation 正确分层？**
   **是。** 两个独立 dataclass、独立字段集；capture 侧无 request id / proposal / generation / epoch；`bind_read_carrier` 对错 namespace 直接 `TypeError`；兼容关系由 route fingerprint + 4 项 runtime 比对显式表达；无 `generation_id=0` 冒充。

3. **capture dummy actual binding 是否真的被控制/观测？**
   **既未控制也未观测 —— 明确 BLOCKED。** Ascend 在 provider 存在时对 capture 直接硬失败；上游 dummy metadata 在 vLLM 内部生成、无可注入入口。**不能记为 capture carrier PASS**；按 §5 要求记为 `BLOCKED`（这符合 R-REPO-01 下的诚实处理）。

4. **replay→consumer→update 有没有 one-step-lag 风险？**
   **没有静态可证的风险，且 P6 拒绝给出结论。** 我重新确认顺序是 `REPLAY → CONSUMER → UPDATE`（未被偷换）；`consumer_generation_ids`/`update_effective_generation_ids` 恒为 `None`，`assert_update_effective_for` 恒抛错；host 侧对象 identity 在 replay 前与 UPDATE 各校验一次，可发现 Python 侧串代。**device-effective one-step lag 仍是 NPU 问题**（timeline 文档的 one-step-lag policy 与我的判断一致）。

5. **backend attribution 是否来自实际 backend？**
   **是。** 在 `update_full_graph_params` 内 `get_impl_cls()/get_builder_cls()` 之后、调用 backend 更新之前派生；要求精确 `AscendAttentionBackendImpl`（子类/未知实现 fail closed）；与 carrier fingerprint 的 backend/builder 逐项比对；未知即 `UNRESOLVED` 并抛错。

6. **Target/write 是否仍严格 full/isolated？**
   **是。** carrier 只含 read tensor；共享 isolation oracle 覆盖 nested object / Tensor storage / NumPy；测试断言 Target root/layer/nested/slot/positions/query/canonical 全部不变；P6 模块无任何 Target 写入。

7. **Graph user Gate 是否仍 fail closed？**
   **是。** `draft_window.py:880` 未被改动；`install_*`/`register_capture_identity`/`bind_read_carrier` 在 production 中零调用 ⇒ 4 个生产 wrapper 全为 no-op ⇒ 生产行为零变化；`FULL/FULL_DECODE_ONLY/PIECEWISE` 的 Window ON 仍未开放，且无任何 NPU 证据。

---

## 17. 最终裁决

```text
P6 REVIEW VERDICT:

HOLD — REPOSITORY/ARCHITECTURE BLOCKER
```

> 说明（避免误读）：这**不是** P6 代码的正确性缺陷。replay/update 侧的 read carrier、capture/runtime identity 分层、per-consumer 契约、backend attribution、timeline 诚实性均经我独立核实成立（详见 m-01…m-04 仅 4 项 Minor）。HOLD 的原因是 **capture carrier 注入点在 R-REPO-01 + pinned vLLM 下不可实现（Q-01）**，因此 P6 无法把 Graph Window 推进到任何 enablement；该阻塞必须由 owner 在三条路径中裁决。若 owner 的意图仅是"静态 foundation"，则代码侧应为 `APPROVE WITH REQUIRED FIXES`（修 m-01 的 write-side parity 断言，并落实 m-03 的文档化）。

```text
P6 GRAPH READ CARRIER:
VERIFIED_STATIC

P6 CAPTURE PATH:
BLOCKED

P6 REPLAY TIMELINE:
STATIC_ONLY

GRAPH USER GATE SHOULD:
REMAIN FAIL-CLOSED
```

**停止。未修改任何 production 代码；未替 Codex 修代码。**
