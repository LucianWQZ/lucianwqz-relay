# P7-E Eager Completion — Independent Review

- Reviewer: DeepSeek（独立 Reviewer；未修改任何 production 代码；未使用 Codex 总结/Matrix/测试数字作为事实源）
- Date: 2026-10-14
- Subject: `7feb6de`（P7-E）相对 `7599497`（P6 Final）的 6 文件 / +1690 −17
- Method: 重读真实 source/diff/tests，独立运行测试与自建反例探针；Codex 文档仅作为 §10 的被审计对象

## 0. 结论摘要（Mandated Answers）

| 问题 | 回答 |
|---|---|
| `GRAPH FREEZE PRESERVED?` | **YES** |
| `METHOD MATRIX FACTUAL?` | **YES**（1 处词汇性不一致：plain Eagle，见 Q-01） |
| `BACKEND MATRIX FACTUAL?` | **YES**（无平台行 → F-01） |
| `PARALLEL MATRIX FACTUAL?` | **YES** |
| `ASYNC STATIC CONTRACT?` | **PASS**（附 F-02） |
| `G-MIXED STATUS?` | **STILL PRESENT / NOT ADMISSION-LIMITED**；矩阵已如实标注 `OWNER_BLOCKED` + `RELEASE_BLOCKER` + `FEATURE RELEASE: HOLD`，**无过度声明** |
| `READY_FOR_NPU ROWS VALID?` | **NEEDS CORRECTION**（缺平台维度，F-01） |
| `P8-E ENTRY?` | **READY**（仅指 NPU 证据阶段；release 门仍为 HOLD） |

Findings：**0 Critical / 1 Major / 2 Minor / 3 Question**。

```
P7-E REVIEW: APPROVE WITH REQUIRED FIXES
（Required fix = F-01：补平台门 或 在矩阵增加 310P 行；F-02/F-03 为 Minor；
  Q-01/Q-02/Q-03 为 owner 决策项，不阻塞本阶段）
```

---

## 1. Baseline 独立验证（VERIFIED）

| 项 | 实测 |
|---|---|
| vLLM HEAD | `84030bbe3d74d99bad477a3d2e37a973ccd8865c`，tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`，`git status --porcelain` 空 |
| P7-E commit | `7feb6def64d2dd483627dab6ee5cf7b05d7503f0`，tree `c4b5b47c04cc5f2092ef8771b47c56ce572bb060` |
| P7-E parent | `7599497ab2694c4cf343f61f82f449980d8bad93`（= P6 Final，精确匹配） |
| P6A production commit | 无（`git log --all --grep=P6A` 为空）→ P7 parent 直接落在 P6 Final 上，无 P6A 中间产物 |
| Ascend 工作区 | clean |

改动面（`git diff --name-status 7599497 7feb6de`）：production 仅 3 个文件 —— `spec_decode/draft_window.py`（+130/−17）、新增 `spec_decode/draft_window_async.py`（331）、新增 `spec_decode/draft_window_eager_capability.py`（409）；其余 3 个为测试文件。

**Graph capture 是否被 P7 修改：没有。** 三个 production 文件均与 capture 路径无关：diff 中没有 `aclgraph.py` / `draft_window_graph.py` / `speculator.py` / `attn_utils.py` / `acl_graph.py` 的任何行。

---

## 2. Graph Freeze 是否保持（逐项取证）

| 检查项 | 结果 | 证据 |
|---|---|---|
| `graph_mode != NONE` 仍 reject | ✓ | `draft_window_eager_capability.py:250-255` → `FAIL_CLOSED`（对任意非 `"NONE"` 字符串成立，含 FULL / FULL_DECODE_ONLY / PIECEWISE / FULL_AND_PIECEWISE）；判定结果经 `require_live_materialization()`（`:116-125`）在**任何 P2/P3 分配之前** raise |
| 判定时机早于 FullSource/workspace | ✓ | `draft_window.py:1327-1339`：`evaluate_...` → `require_live_materialization()` raise，之后才 `require_single_group_direct_prefix()` / `build_full_draft_kv_source` / workspace；测试 `test_async_source_capability_stops_before_full_source_allocation` 用 monkeypatch 断言 `build_full_draft_kv_source` 从未被调用，我复现通过 |
| P2 侧的旧闸是否仍在 | ✓ | `draft_window.py:878-881`（`graph_mode != "NONE"` 列为 capability failure）+ `:150-172`（任一 failure → `NotImplementedError`）双层保留 |
| 是否安装了 P6 graph provider | **否** | `install_draft_window_graph_binding_provider` 定义在 `draft_window_graph.py:1443`，全仓非测试目录无调用者（`grep` 复核）；P7 未新增任何安装点 |
| 是否新增 capture-scoped state | **否** | 新增状态只有 `P7EagerTopologyFingerprint`（`draft_window_eager_capability.py:35-105`，纯 route/topology attestation）与 execution-lane 化的 lease pool；两者都不参与 capture |
| 是否修改 P6A 冻结边界 | **否** | P6A 冻结产物（`observe_draft_window_graph_capture` / `consume_draft_window_graph_metadata` / carrier）在 P7 diff 中零改动 |

未发现任何绕过路径。**GRAPH FREEZE PRESERVED = YES。**

---

## 3. Policy（逐 method 独立验证）

源码：`draft_window.py:610-672`（`resolve_draft_window_policy`，P1 代码，P7 未改）+ `spec_decode/__init__.py:30-77`（唯一应用点）。

| method | 行为 | 证据 |
|---|---|---|
| MTP | `FORCED_OFF`，且在**任何数值校验之前**返回（即使 window 数非法也强制 OFF） | `draft_window.py:633-641`；warning 文案 `__init__.py:79-93` |
| DeepSeek-V4 共训 DSpark | `FORCED_OFF` | `draft_window.py:643-651`（`_is_deepseek_v4_target` 在 `:605-608`） |
| plain Eagle | **`NotImplementedError`（配置即拒）** | `draft_window.py:645-646` ← 与矩阵 `OWNER_BLOCKED` 不一致，见 Q-01 |
| Eagle3（static K） | `ELIGIBLE_ON` | `draft_window.py:648-664` |
| DFlash / eligible DSpark | `ELIGIBLE_ON` | 同上 |
| Eagle3 dynamic-K | `OWNER_BLOCKED`（P7）→ raise（production） | `draft_window_eager_capability.py:238-243`；`resolve_static_future_offset:681-682` 另有独立 raise |
| DFlash2 | `FAIL_CLOSED` | `draft_window_eager_capability.py:244-249` |
| 未知 method | `NotImplementedError` | `draft_window.py:648-651` |

**Backend 能力不得覆盖 policy：成立。** `evaluate_...` 对 `CONFIG_OFF` / `FORCED_OFF` 在函数最前直接返回且 `topology_fingerprint=None`（`:221-228`），无法被后续 backend/layout 结论“升级”；且 `build_draft_window_source_capability` 仅在 policy 为 `ELIGIBLE_ON` 时才被调用（`_configure_draft_window` 只在 `__init__.py:104` 的 eligible 分支执行，`_initialize_draft_window_source_capability` 在 policy 缺失时直接 return —— 见 `dflash/speculator.py:47-51` 同构实现）。

---

## 4. Backend 逐 route 反查

分类器：`draft_window.py:849-877`（P2，P7 未改）。P7 的 backend 门在 `draft_window_eager_capability.py:283-296`（DSA/SFA/MLA/NATIVE_OR_RECYCLING 一律 `FAIL_CLOSED`）+ `:336-342`（非 dense direct-prefix 一律 `FAIL_CLOSED`）。

| route | 我的独立结论 | 证据 |
|---|---|---|
| **DSA** | 未做 table/length/indices/SAS/native/compressor/QLI/resident/lifetime 的 typed 契约，**FAIL_CLOSED 成立** | `draft_window_eager_capability.py:283-296` 的 reason 即 `V_final = V_draft ∩ V_native ∩ V_resident`；`_classify_layout:850-851` 覆盖 `AscendDSABackend` 及其子类（`dsa_v1.py:276/288` 的 C4/C128） |
| **SFA** | main 与 indexer 均无 typed visible-count / index translation，**FAIL_CLOSED 成立** | `_classify_layout:854-855` 覆盖 `AscendSFABackend` + `AscendSFAIndexerBackend` |
| **MLA** | 未独立证明 exact/upper/padding/operand，**FAIL_CLOSED 成立** | `_classify_layout:852-853`（backend 或 `MLAAttentionSpec`） |
| **V4** | 未使用旧 `dsa_v41.py` 路径（该文件不存在），走当前 owner（`dsa_v1`/`sfa_v1`/`indexer`）| `ls vllm_ascend/attention/` 无 `v4*`；分类器只 import 当前 backends（`draft_window.py:35-38`）。**但 V4 无显式模型门 → Q-03** |
| **Recycling（native SWA/circular/chunked）** | **FAIL_CLOSED 成立**；未发现错误 `min` 公式 | `_classify_layout:856-864` 覆盖 `ChunkedLocalAttentionSpec/CircularBufferSpec/RSWASpec/SlidingWindowSpec` 及带 `sliding_window/attention_chunk_size` 的 `FullAttentionSpec`。全模块唯一的 `min` 出现在 DCP clamp（`:367`），已独立验证与 vLLM 完全一致（见 §6） |
| 缺关键 consumer 时降级 | ✓ | `:262-267`（无 group）、`:330-335`（group 数 ≠1）、`:324-329`（inventory/group failure 非空）。FA3（`AscendFABackend` 不是 `AscendAttentionBackend` 子类）由 P2 的 `draft_window.py:983-984` group failure 拦下 → 同样 FAIL_CLOSED |

**唯一缺口是平台维度**：判定完全基于类关系与配置标志，无 310P/设备门 → **F-01**。

---

## 5. Multi-group

| 检查项 | 源码事实 |
|---|---|
| absolute S | ✓ `SingleGroupDirectPrefixProvider._describe_interval` 以“previously validated **absolute** interval”（`draft_window.py:531-539`）投影，descriptor 携带 `source_start_column`/`required_columns`（`:576-586`） |
| per-gid provider | 仅允许单 gid：`inventory.require_single_group_direct_prefix()`（`:150-179`）+ P7 `:269-281` |
| valid count | `gather_valid_num_blocks*`（`:1125-1215`）+ `DraftMetadataInputs.__post_init__` 校验 `valid_num_blocks` int32/1-D/padded 行数（`:1861-1879`） |
| alias | `_shares_storage`（`:1223-1231`）+ `validate_draft_metadata_isolation`（`:2358`，在 `DraftMetadataStore.publish` 内调用 `:1937-1946`） |
| homogeneous multi-group | `FAIL_CLOSED`（`draft_window_eager_capability.py:277-281`）；P2 另有 `len(consumer_gids) > 1` → failure（`draft_window.py:1014-1020`） |
| heterogeneous multi-group | `OWNER_BLOCKED`（`draft_window_eager_capability.py:271-276`，`_is_heterogeneous` 在 `:197-208`） |
| 同一 gid 多 consumer | `FAIL_CLOSED`（P2 `draft_window.py:1023-1029`）+ P7 `:330-335` |
| 是否为支持 multi-group 而改 legacy semantics | **没有**：P7 diff 未触碰 P2 inventory/provider/legacy 语义 |

---

## 6. Parallel（含 DCP 独立反查）

源码门：`draft_window_eager_capability.py:298-319`（TP/DP/PP/PCP/DCP ≠1、SP、DSA-CP、FlashComm 任一成立 → `FAIL_CLOSED`）。

| 维度 | 矩阵 | 源码 | 一致 |
|---|---|---|---|
| TP/DP/PP/PCP >1 | FAIL_CLOSED | `:299-307` | ✓ |
| DCP >1 | FAIL_CLOSED | `:299-307` | ✓ |
| SP / DSA-CP / FlashComm | FAIL_CLOSED | `:308-313` | ✓ |
| rank projection / topology identity | 见下 | | |

- **topology identity**：`P7EagerTopologyFingerprint` 记录 method/route/backend/builder/gids/layouts/geometry/五维 world size/SP/DSA-CP/FlashComm/graph/async/prefix-cache/provider_version/lane（`draft_window_eager_capability.py:35-58`），并流经 capability → runtime → generation identity（`draft_window.py:594, 1361, 1395, 2043, 2126`）。**注意**：标准路径只记录不校验 → **F-03**。
- **write/full slot**：`DraftMetadataInputs` 明确不含 slot/positions/Target（`draft_window.py:1822-1830` docstring），slot 走 `block_tables.compute_slot_mappings`（全物理槽），P7 未新增任何 slot 来源。
- **lifecycle**：见 §7。

**DCP 独立反查（针对“特别尝试找 DCP 错误整除”）**：我把 `draft_window_eager_capability.py:356-368` / `:371-409` 的源码文本抽出后与 vLLM 真实内核对照，穷举 W≤8、interleave≤8、rank<W、length<400：

```
local-prefix mismatches vs vLLM kernel: 0
interval mismatches vs per-position ownership: 0
cases where local(E)-local(S) differs from naive V//W: 1100
```

即：`rounds = L//I//W` 与 vLLM `L//(W*I)` 恒等（`floor(floor(L/I)/W) == floor(L/(W*I))`），clamp 亦逐位相同；`local_visible_length = local(E) − local(S)` 与逐位置归属计数完全一致，且与错误公式 `V//W` 在 1100 个样本上不同。**未发现 DCP 错除；反而证明该 helper 正确避开了 `V//W` 陷阱。** 该 helper 目前无 production 调用者（DCP 已被 FAIL_CLOSED），属“为未来保留的参考实现”，其正确性已由本次验证背书。

---

## 7. Async：主动构造状态反例（自建探针，非引用 Codex 测试）

探针方式：加载 UT conftest 的 mock 环境 + 复用测试 helper 构造 pool，逐项断言（脚本见附录）。

| 反例 | 我的观测 | 判定 |
|---|---|---|
| delayed completion | `submit` 后 `poll=False` 直到 token 完成 | ✓ 无提前复用 |
| reverse completion | lane1 先完成后可独立 `poll/retire/release`；lane0 仍 pending | ✓ 车道独立 |
| **abort after submit**（token 永不完成） | `abort` 只置 `abort_requested=True` 且保持 `SUBMITTED`；下次 `acquire` → `RuntimeError: draft-window async pool pressure: all N lanes are owned`（`draft_window_async.py:127-130`） | ✓ fail-closed（车道被永久占用而非复用） |
| active lane reuse / stale handle | `release` + 同 lane 重新 `acquire` 后，旧 handle 的 `materialize/poll/release` 全部被 `_require_active` 拒绝（`:319-322`） | ✓ |
| active lane reuse（真实并发） | 两个 in-flight 操作落在不同 lane，且 backing 地址**互不相同**；释放后同 lane 复用**同一地址**但 `generation_id` 递增 | ✓ 稳定地址 + 无陈旧代际 |
| pressure | 满容量即 `RuntimeError`（非阻塞） | ✓ |
| preempt/resume | 新 generation + backing 地址不变（测试 `test_preempt_resume_...` 覆盖，我复现） | ✓ |
| stale request / epoch | `mapping_epoch` 必须严格递增（`:113-117`），请求 ID 必须唯一非空（`:118-122`） | ✓ |
| backend-derived late reader | `bind(..., backend_derived_buffers=...)` 只做类型检查，**无 alias/owner 校验**；我把 `inputs.window_block_table` 作为该字段传入并被接受 | ✗ **F-02** |
| host/fake-event 是否被限制在 STATIC_READY | ✓ `async_scheduling=True` → `STATIC_READY`（`draft_window_eager_capability.py:343-348`）→ `require_live_materialization()` raise；`draft_window_async.py` 在 production 中**零 import**（全仓 grep 仅 tests） | ✓ 契约自洽 |

补充：`submit` 中若 completion 查询抛异常，状态机保持 `_active_inputs` 与 `READER_PENDING`（`draft_window.py:2256-2273` 的 `_retire_lease` 在 `_lease_pool.retire` 抛错时尚未清空 `_active_inputs`），因此 `poll` 可安全重试（`DraftMetadataStore.discard` 对空 entry 幂等，`:1953-1959`）——我复核了这条路径的状态一致性，未发现悬挂。

**ASYNC STATIC CONTRACT = PASS**（含 F-02 待补）。

---

## 8. G-MIXED

| 问题 | 独立结论 | 证据 |
|---|---|---|
| 是否真正解决 | **否** | mixed prefill/decode → `NotImplementedError("MRV2 draft-window P4a does not support mixed prefill/decode proposals")`（`draft_window_eager.py:557-580`，raise 在 `:579`） |
| 是否被安全 admission 限制 | **否** | 全仓 `grep admission\|single_active\|num_reqs > 1` 无命中；无单活跃请求限制、无批次形态准入 |
| 是否仍存在 | **是**，且抛错点在 EngineCore 请求路径上（proposal scope 内） | `draft_window_eagle3.py:153`（调用点）在 `:164`（`epoch_source.begin`）之前 → **不分配任何 window 状态**（这点是好的：不会留下脏状态） |
| 是否 owner 未决 | **是** | 矩阵 §6/§8 已写 `OWNER_BLOCKED` / `RELEASE_BLOCKER` / `FEATURE RELEASE: HOLD` |
| Matrix 是否因此写了 release candidate | **没有** | 矩阵末段为 `FEATURE RELEASE: HOLD`、`P7-E NPU: NOT VERIFIED by P7`，无 `SUPPORTED` 行 |

→ 不构成 Critical/Major（矩阵如实、无过度声明）。列为 **Q-02（owner 决策）**。

---

## 9. Target / write 新增路径

- P7 diff **没有**新增任何 Target/slot/positions/query/FullSource 路径：新增字段仅 `eager_topology_fingerprint`、`execution_lane`、`_pending_retirement_identity`、`poll_reader_completion`、`reclaim_completed_reader` 签名变化。
- “Window table 当 slot source”攻击面：`DraftMetadataInputs` 明确拒绝携带 slot/positions/Target（`draft_window.py:1822-1830`）；publish 必经 `validate_draft_metadata_isolation`（`:1937-1946`）。我的探针验证：把 window read table 同时作为 draft metadata 与 target metadata 提交时被 isolation oracle 拒绝（`PASS`）。
- 唯一例外是 async 的 `backend_derived_buffers`（**F-02**）——它是 P7 新增的、绕过该 oracle 的 tensor 入口，当前无消费者。
- P7 对 P3 reuse 纪律是**收紧**而非放松：`_reclaim_completed_reader` 移到 state 层显式调用（`draft_window.py:2152, 2077, 2040`），`reclaim_completed_reader` 由“静默 return”改为**抛错**（`:1797-1813`），并新增 `_pending_retirement_identity` 确保 pending reader 永不被静默回收（`:2281-2294`）。我复核了所有 `_lease_pool.acquire/retire` 调用点（`:2152, 2169, 2201, 2242, 2266, 2281, 2292`），未发现“acquire 不再自动回收”导致的回收缺失路径。

---

## 10. Capability Matrix 反向审计

被审计对象：`P7_Eager_Capability_Matrix.md`（+ 源码 `draft_window_eager_capability.py`）。

| 矩阵行 | 我的独立验证 | 结论 |
|---|---|---|
| `CONFIG_OFF`（无配置，zero state） | `resolve_draft_window_policy:625-632` + `_initialize_...` 在 policy 缺失时 return | ✓ |
| `FORCED_OFF`（MTP / V4 共训 DSpark，zero state） | §3 表 | ✓ |
| `OWNER_BLOCKED`（dynamic-K / heterogeneous multi-group / plain Eagle / G-MIXED） | dynamic-K `:238-243`；heterogeneous `:271-276`；plain Eagle 见 Q-01；G-MIXED 见 §8 | 3/4 直接对应源码；plain Eagle 为词汇性偏差 |
| `FAIL_CLOSED`（DFlash2 / graph / prefix cache / 复杂 layout / 非 1 拓扑 / 无 consumer / homogeneous multi-group） | `:244-342` 逐条对齐 | ✓ |
| `STATIC_READY`（async） | `:343-348` + async 模块无 production import | ✓ |
| `READY_FOR_NPU`（单 group dense-GQA、graph NONE、非 async、全 1 拓扑、无 flags） | `:269-353` | ✓ 但**缺平台约束** → F-01 |
| §5 “prefix cache ON → rejects before source/workspace” | prefix 检查在 `:256-261`，早于 FullSource（`draft_window.py:1339-1345`） | ✓ |
| §2 backend 矩阵 8 行全 FAIL_CLOSED | §4 表 | ✓（粒度比源码粗，状态无过度声明） |
| §4 parallel 矩阵 | §6 表 | ✓ |
| §8 `FEATURE RELEASE: HOLD` / `NPU: NOT VERIFIED` | 与源码及我的验证一致 | ✓ 无 overclaim |

**UNJUSTIFIED_READY_FOR_NPU**：未发现（除 F-01 的平台外延问题）。
**MISSING_GATE**：**F-01（平台维度）**。
**OVERCLAIMED_ROUTE**：未发现。

---

## 11. 独立测试（全部为我本地重跑，环境问题单列）

| 范围 | 命令 | 结果 |
|---|---|---|
| P7 targeted | `pytest -q tests/ut/spec_decode/test_draft_window.py test_draft_window_async.py test_draft_window_eager_capability.py` | **176 passed** |
| full spec_decode | `pytest -q tests/ut/spec_decode/` | **582 passed, 13 skipped, 7 failed** |
| block tables | `test_block_table.py` + `worker/v2/test_v2_block_table.py` | **14 passed**（21 subtests） |
| backend/attention | `pytest -q tests/ut/attention/` | **472 passed, 3 skipped** |
| parallel | `pytest -q tests/ut/distributed/` | **572 passed**（284 subtests） |
| worker v2 | `pytest -q tests/ut/worker/v2/` | **31 passed** |
| static-ish | `test_dependency_documentation.py` + `test_envs.py` + `test_utils.py` | 43 passed / 1 failed / 1 skipped |
| P1–P6 regression | 由上述 full spec_decode 覆盖（P1–P6 全部 window 测试在内） | 与 P6 基线一致 |

两个失败簇，均**非 P7 回归**：

1. `test_speculators_vwn_eagle3.py` 7 项：`ValueError: Invalid attention backend for None`（`vllm/v1/attention/selector.py:208`）——宿主机无 NPU 的**环境问题**；该测试文件对 `draft_window` 零引用，且与 P6 审查时的同数同因一致。
2. `test_utils.py::TestUtils::test_vllm_version_is`：本环境必须设 `VLLM_VERSION=0.29.0`（否则 collection 直接失败：`Invalid vllm version dev`），而该用例断言安装版本为 `1.0.0` → **环境与本用例互斥，按 §11 记为 NOT RUN（环境冲突，非代码缺陷）**。

---

## 12. Findings

### F-01 — **Major** · MISSING_GATE：能力判定缺平台维度，310P 可被判 `READY_FOR_NPU`
- **Source**：`draft_window_eager_capability.py:283-353`（判定依据仅为 backend/builder/kv_spec 的类关系 + 配置标志）；`grep -n "is_310p\|310" vllm_ascend/worker/v2/spec_decode/draft_window*.py` → **无命中**；矩阵亦无平台维度。
- **Behavior**：310P 上 `platform.py:258` 选择 `AscendAttentionBackend310`（`_310p/attention/attention_v1.py:48`，`AscendAttentionBackend` 子类）与 `AscendAttentionMetadataBuilder310`（`_310p/attention/metadata_builder.py:51`，`AscendAttentionMetadataBuilder` 子类）→ 满足 `_classify_layout:867-875` 与 P2 group 检查（`draft_window.py:983-996`）→ `DENSE_GQA_DIRECT_PREFIX` → 其余门（单 group、全 1 拓扑、graph NONE、无 async/prefix cache）若成立即返回 `READY_FOR_NPU`（`:337-353`）。310P 的 speculator 走同一 `init_speculator`（`patch/worker/patch_v2/patch_spec_decode_310.py:39-52` 对非 MTP 直接委派 `_orig_init_speculator`）。
- **Contract**：`READY_FOR_NPU` 定义为“local source/static contract is closed for **an exact route**”；该 “exact route” 目前不含平台约束。
- **Reproduction**：静态推导（类关系 + `platform.py:258`）；NPU 侧可复现为“310P + `draft_window_size` + 受支持 spec method → window 进入 live eager 路径”。
- **Correction**：二选一 —— (a) 在 capability 增加显式平台门（如仅允许 A2/A3 类设备），或 (b) 在矩阵增加 310P 行并置 `FAIL_CLOSED`（并说明依据）。需 owner 决定平台归属。
- **Owner/NPU 影响**：本阶段所有“未验证即 fail closed”的姿态在平台维度上出现盲点；若 310P 的 FIA/metadata 契约与 A2/A3 不同，用户显式配置即可进入未验证路径。*（我未发现 310P 上必然出错的证据，故定为 Major 而非 Critical。）*

### F-02 — **Minor** · async `backend_derived_buffers` 无 alias/owner 校验
- **Source**：`draft_window_async.py:190-218`（仅 `isinstance(..., torch.Tensor)` 检查，`:201-206`），随后 `:217` 存入 handle，`release` 时清空（`:269`）；全仓无消费者。
- **Behavior**：我的探针把 `inputs.window_block_table` 作为该字段传入 → **被接受**（“alias check: ABSENT”）。这是 P7 新增的唯一绕过 `validate_draft_metadata_isolation`（`draft_window.py:1937-1946`）的 tensor 入口。
- **Contract**：与 §9“Window table 不得充当 slot/write source”的要求冲突（当前因无消费者而无实际写路径）。
- **Reproduction**：`/tmp/p7probe/async_probe.py` case 6。
- **Correction**：在 `bind` 内用 `_shares_storage`（`draft_window.py:1223-1231`）拒绝与 workspace/window read table 共享 storage 的 buffer；或在接入 live 前给出该字段的 owner 契约。
- **Owner/NPU 影响**：接入 async live 路径前必须补齐。

### F-03 — **Minor** · 标准路径只记录、不校验 `topology_fingerprint`
- **Source**：写入 `draft_window.py:2043`、refresh 复制 `:2126`、runtime 保存 `:1985-1987`；`DraftWindowGenerationIdentity.__post_init__`（`:1397-1426`）不校验该字段；标准路径无任何“identity vs runtime fingerprint”断言（仅 async 在 `draft_window_async.py:179-181, 310-317` 校验）。
- **Behavior**：因 runtime fingerprint 构造期固定、refresh 复制上一代，现网不会漂移 → 无现网缺陷；但现有代码无法**证明**该不变量。
- **Correction**：在 `_materialize_identity` 增加一致性断言（或在 `__post_init__` 要求非 `None`），使 “topology identity” 从 attestation 升级为 enforced invariant。
- **Owner/NPU 影响**：P8 NPU 证据阶段需要该不变量作为“同一 exact route”的判据。

### Q-01 — **Question** · plain Eagle：矩阵 `OWNER_BLOCKED` vs 源码硬拒
矩阵 §1 写 plain Eagle = `OWNER_BLOCKED`；源码在 `resolve_draft_window_policy` 直接 `NotImplementedError`（`draft_window.py:645-646`），**永远不会到达** P7 的 `OWNER_BLOCKED` 分类（`P7EagerCapabilityStatus` 中无对应路径）。请 owner 明确期望：(a) 保持“配置即被拒”（当前行为），或 (b) 改为“可配置但强制 OFF / owner 待决”。

### Q-02 — **Question** · G-MIXED 需 owner 决策
见 §8：仍然存在、无 admission 限制、矩阵已如实标为 `RELEASE_BLOCKER`。需 owner 在“general support”与“early single-active restriction”之间选择；在此之前 release 门应保持 HOLD。

### Q-03 — **Question** · V4 无显式模型门，安全性依赖 composition 分类
`_is_deepseek_v4_target` 只用于 DSpark 共训策略（`draft_window.py:605-608, 643-651`）；V4 的其他组合走通用分类 `_classify_layout`。矩阵 “V4/V4.1 combinations → FAIL_CLOSED” 因此是**推导值**而非独立门。请 owner 确认不存在“V4 目标 + 形状为 dense-GQA 的 draft 层”的可达组合；若存在，该组合会被判 `READY_FOR_NPU`。

---

## 13. 最终裁定

```
GRAPH FREEZE PRESERVED?      YES
  （P7 未触碰 capture 路径；graph_mode != NONE 双层 reject；P6 provider 仍未安装；
    require_live_materialization 在 FullSource/workspace 之前 raise，已被测试与我复核确认。）

METHOD MATRIX FACTUAL?       YES   （唯一偏差为 plain Eagle 的词汇状态，Q-01）
BACKEND MATRIX FACTUAL?      YES   （FAIL_CLOSED 全部成立；缺平台行 → F-01）
PARALLEL MATRIX FACTUAL?     YES   （DCP helper 与 vLLM 内核逐位一致，0 mismatch）
ASYNC STATIC CONTRACT?       PASS  （自建反例 8 类全部符合 fail-closed 预期；缺 backend_derived_buffers alias 校验 → F-02）

G-MIXED STATUS?              STILL PRESENT / NOT ADMISSION-LIMITED / OWNER_BLOCKED
                             （矩阵如实标为 RELEASE_BLOCKER，FEATURE RELEASE: HOLD → 不构成过度声明）
READY_FOR_NPU ROWS VALID?    NEEDS CORRECTION（补平台维度，F-01）
P8-E ENTRY?                  READY（NPU 证据阶段可进入；release 门保持 HOLD 直到 G-MIXED 与 F-01 决策完成）

P7-E REVIEW:                 APPROVE WITH REQUIRED FIXES
  Required: F-01（补平台门 或 增加 310P 行）
  Recommended: F-02、F-03
  Owner decisions: Q-01、Q-02、Q-03
```

---

## 附录 A — 复现命令

```bash
cd /Users/wenqingzhang/Desktop/vllm/vllm-ascend
git rev-parse HEAD HEAD^{tree}                      # 7feb6de... / c4b5b47c...
git log -1 --format=%P HEAD                         # 7599497...（P6 Final）
git diff --stat 7599497 7feb6de

run() { env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q "$@"; }
run tests/ut/spec_decode/test_draft_window.py \
    tests/ut/spec_decode/test_draft_window_async.py \
    tests/ut/spec_decode/test_draft_window_eager_capability.py   # 176 passed
run tests/ut/spec_decode/                                        # 582 passed, 7 failed(env)
run tests/ut/attention/                                          # 472 passed
run tests/ut/distributed/                                        # 572 passed
run tests/ut/worker/test_block_table.py tests/ut/worker/v2/test_block_table.py
```

独立反查脚本（自建，未写入仓库）：

- `/tmp/p7probe/dcp_check2.py` —— 从源码文本抽取 `_dcp_local_prefix_length` / `project_dcp_window_interval`，与 `vllm/v1/worker/gpu/cp_utils.py::_dcp_local_seq_lens_kernel` 穷举对照（0 mismatch）并验证 `local(E)-local(S)` 语义。
- `/tmp/p7probe/async_probe.py` / `async_probe2.py` —— 复用 UT helper 复现 §7 的 8 类反例（abort-after-submit 压力、stale handle、双 lane 独立 backing、反向完成、isolation oracle、`backend_derived_buffers` alias 缺口）。
