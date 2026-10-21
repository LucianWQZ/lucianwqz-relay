# P4a Ascend-only Eager Integration Implementation Notes

## 1. Repository Boundary

### 1.1 Document status

| Item | Value |
|---|---|
| Final Design | `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md` |
| Implementation Plan | `MRV2_Draft_Window_Implementation_Plan.md` |
| Frozen repository rule | `R-REPO-01: production may modify vllm-ascend only` |
| exact vLLM baseline | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM active checkout | baseline HEAD；`git status --porcelain` empty |
| vLLM-Ascend P3 Final | `16727882744c935d9e899f7775353b57738852bc` |
| Ascend-only P4a C4 | `0dd83e9f75d4b2d766126af3a7f92352e342f756` |
| C4 title | `feat(spec-decode): integrate MRV2 draft windows in Ascend eager path` |
| C4 parent | exact P3 Final `16727882744c935d9e899f7775353b57738852bc` |
| review-fix commit | `4c1f69146915f4f0ae5a6a61371ebfe181237d8f` |
| review-fix title | `fix(spec-decode): address P4a Ascend-only review findings` |
| implementation status | **ASCEND-ONLY STATIC FINAL: PASS** |
| `G-ASCEND-ONLY-INTEGRATION` | **STATIC CLOSED；independent review adjudicated** |
| `G-GQA-EAGER` | **OPEN；NPU oracle/profiler not run** |
| P4b / Graph / Async | **NOT STARTED / BLOCKED** |
| release | **HOLD** |
| document time | 2026-10-10 16:34:39 +0800（Asia/Shanghai） |

只有vLLM-Ascend C4及其独立review-fix lineage是当前交付实现。vLLM没有production或
test改动，也不需要公司服务器安装私有vLLM patch。

### 1.2 Archived prototypes

| Repository | Archive ref | Commit | Conclusion |
|---|---|---|---|
| vLLM | `archive/p4a-upstream-hook-prototype` | `0403469280c3d0f19c55cd1768e7e9d9e566a719` | explicit vendor-neutral hook技术上可行，但违反repository boundary |
| vLLM-Ascend | `archive/p4a-upstream-dependent-prototype` | `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529` | 功能prototype依赖上述私有API，不能作为delivery commit |

历史diff与测试结论继续保存在：

- `P4a_vLLM_Upstream_Hook_Full_Diff.patch`；
- `P4a_vLLM_Ascend_Full_Diff.patch`；
- `P4_Draft_Attention_Eager_Integration_Implementation_Notes.md`，其顶部已标记
  **SUPERSEDED PROTOTYPE**。

当前包含P3 Final到C4与review-fix最终状态的可审阅patch为：
`P4a_Ascend_Only_Eager_Integration_Full_Diff.patch`。

prototype证明“显式read input可以保持slot/query/write边界”，但它不再关闭任何production
Gate。

## 2. What Survived from Prototype

以下经过CPU/static验证、且不依赖修改vLLM的能力从prototype重新移植到P3 Final之上：

- production proposal-owned monotonic `mapping_epoch`；
- ordered `req_ids`与`idx_mapping_np` fingerprint；
- P1 scalar plan、P2 direct-prefix descriptor和canonical FullSource；
- P3 fixed workspace、lease、typed `DraftMetadataInputs`和
  `DraftMetadataStore`；
- single validation boundary；
- DFlash apply-time `K+1`和DSpark真实`K`/`K+1` query width；
- controlled full-exact host snapshot；
- Target nested/storage isolation；
- fail-closed topology/backend/prefix/prefill matrix；
- optional Ascend CPU-exact metadata seam。

没有移植：

- upstream `DraftAttentionReadInputs`；
- upstream protected builder adapter；
- upstream method signature变化；
- 对`040346928…`的任何import、feature detection或fallback；
- prototype的“`G-LIVE-HOOK CLOSED`”结论。

## 3. Ascend-only Candidate Analysis

源码调查覆盖：

- baseline
  `vllm/v1/worker/gpu/spec_decode/speculator.py::_build_draft_attn_metadata`；
- baseline
  `vllm/v1/worker/gpu/spec_decode/dflash/speculator.py::_build_draft_attn_metadata`；
- `AscendDFlashSpeculator`、`AscendDSparkSpeculator`及其MRO；
- `build_attn_metadata_wrapper()`和
  `build_draft_attn_metadata_factory()`；
- `worker/v2/attn_utils.py::build_attn_metadata()`；
- real eager `propose -> prepare -> metadata -> forward` chain。

| Candidate | Correctness | Explicit transport | No shared mutation | OFF parity | Upstream drift | Testability | Maintainability | Verdict |
|---|---|---|---|---|---|---|---|---|
| A — full Ascend subclass override | 可逐项实现 | 是 | 是 | OFF可直接super | 高；复制完整assembly | 可测 | 中低 | 不选 |
| B — factory/wrapper carries current Window state | 并发/嵌套难证明 | 否；会变成隐式lookup | 若用closure/global则不满足 | 难做instance differential | 高 | 低 | 低 | **拒绝** |
| C — minimal vendor-local method adapter | 可保持Frozen边界 | **是；instance typed kwargs** | **是** | **OFF exact super** | 中低；只复制read-input selection/kwargs assembly | **高** | **最高** | **选择** |
| D — proxy/fake-self调用upstream implementation | MRO、`super()`和owner语义脆弱 | 部分 | 表面无swap | 不稳定 | 隐式 | 低 | 低 | 拒绝 |

Candidate B与当前已有wrapper机制必须区分：

- baseline wrapper确实临时替换module function，用于选择Ascend metadata builder；
- DSpark factory现有closure只注入positions/is_prefilling；
- rescue没有把Window generation、workspace、table或length存入该global/closure；
- Window数据只存在于当前speculator instance，并作为当前调用的显式kwargs传递。

因此选择C不新增hidden global transport，也不改变baseline wrapper的既有作用。

## 4. Chosen Integration Seam

### 4.1 Owners

| Object | Creator / owner | Lifetime |
|---|---|---|
| `DraftWindowProposalEpochSource` | one Ascend speculator instance | speculator |
| `DraftWindowProposalContext` | outer real proposal | one proposal |
| P3 workspace/runtime/store | same speculator instance | speculator；one active serialized generation |
| `DraftMetadataInputs` | P3 materialize | one generation |
| `AscendDraftAttentionReadInputs` | single validation adapter | one metadata build |
| Draft metadata | existing Ascend builder | one proposal/store generation |
| Target metadata | Target `model_state` | Target-owned；never replaced/mutated |

### 4.2 Real call chain

```text
AscendDFlashSpeculator.propose()
or AscendDSparkSpeculator.propose()
  ↓ existing full prepare_dflash_inputs
full positions / full query layout / full slot mapping / context KV write
  ↓
DraftWindowEagerMixin._draft_window_proposal_scope()
  ↓
epoch + ordered request/mapping fingerprint
  ↓
_materialize_draft_window_read_inputs()
  ├─ one prepared full-exact D2H snapshot
  ├─ P1 Window scalar plan
  ├─ P2 descriptor + CPU canonical valid counts
  └─ P3 lease/workspace/materialize
  ↓
DraftMetadataInputs
  ↓
_validated_draft_attention_read_inputs()
  └─ validate_for(expected_identity) exactly once
  ↓
AscendDraftAttentionReadInputs
  ↓
_build_ascend_draft_attn_metadata()
  ├─ Window block table / device exact / CPU exact / CPU upper
  ├─ canonical full self.block_tables.slot_mappings
  └─ baseline query-start / causal / kv-cache kwargs
  ↓
existing Ascend build_attn_metadata wrapper/factory
  ↓
independent Draft metadata
  ↓
Target alias isolation + DraftMetadataStore.publish(real Target)
  ↓
Draft forward and sampling
  ↓
outer scope retires/aborts generation
```

唯一Window-ON assembly位于
`vllm_ascend/worker/v2/spec_decode/draft_window_eager.py:446`。proposal逻辑、
prepare kernel、slot calculation、model forward和sampling均未复制。

## 5. Why No Upstream Changes Are Required

原版DFlash/DSpark最终通过可override的protected
`_build_draft_attn_metadata()`构造Draft metadata。Ascend类MRO改为：

```text
AscendDFlashSpeculator
  -> DraftWindowEagerMixin
  -> upstream DFlashSpeculator
  -> upstream DraftModelSpeculator
```

DSpark在mixin后继续走upstream
`DSparkSpeculator -> DFlashSpeculator`。因此：

- Window OFF/profile/dummy可直接调用`super()._build_draft_attn_metadata(...)`；
- Window ON可在Ascend override中使用P3 typed inputs；
- final builder仍是现有Ascend `build_attn_metadata`；
- DFlash wrapper和DSpark positions/is_prefilling factory无需新API；
- slot mappings仍从`self.block_tables.slot_mappings`取得；
- positions仍由原DSpark factory注入；
- upstream proposal/forward/sampling无需复制。

专门测试断言原版vLLM不存在prototype symbol，且整个Ascend suite在该状态下import、construct并
运行P1–P4a CPU contracts。

## 6. Duplication / Drift Cost

### 6.1 What is duplicated

Window ON本地复现baseline metadata assembly中的最小片段：

- uniform/non-uniform `query_start_loc_cpu`计算；
- `max_query_len`；
- DCP-local fallback分支（虽然P4a DCP>1在更早Gate拒绝）；
- builder kwargs列表；
- block tables/seq lengths read-input选择。

### 6.2 What is not duplicated

- `propose()`主流程；
- DFlash/DSpark input preparation；
- slot mapping计算；
- context KV write；
- positions构造；
- Attention builder本体；
- model forward、sampling或rejection；
- Graph capture/replay；
- scheduler或Target路径。

### 6.3 UPSTREAM_DRIFT_GUARD

`tests/ut/spec_decode/test_draft_window_eager.py`固定：

- baseline `DraftModelSpeculator._build_draft_attn_metadata` signature；
-该method normalized AST SHA-256
  `91099e775ec44ef5520ca8231fae89ff9a75d2f7386b32d3104774b2ecab8654`；
- baseline DFlash override AST SHA-256
  `0e2df9e2c57ce3d28ea1a311d4956e3a974eec76b3b518cfe3c99292f1a9ad4b`；
- expected kwargs/table/slot/query/step/DCP behavior；
- OFF differential parity。

未来upstream method发生相关变化时，guard应直接失败，维护者必须重新审计local assembly；
不得silent drift。这是`R-REPO-01`带来的明确维护成本。

## 7. Read vs Write Boundary

| State | Window OFF | Window ON | Changed? | Reason |
|---|---|---|---|---|
| Draft read block table | canonical full gathered table | P3 Window workspace table | **Yes** | feature目的 |
| Draft device read length | prepared full exact | Window exact | **Yes** | feature目的 |
| Draft CPU exact | baseline-derived | same-generation Window exact | **Yes** | explicit Ascend seam |
| Draft CPU upper/max | full upper | final Window upper/max | **Yes** | metadata capacity |
| slot mapping values/source | canonical full mapping | canonical full mapping | **No** | write-side Frozen |
| positions | baseline draft positions | same positions | **No** | query Frozen |
| query start/layout | baseline | same baseline formula/buffer | **No** | query Frozen |
| canonical FullSource | canonical owner | same owner/content | **No** | read-only source |
| physical KV allocation/write | baseline full | baseline full | **No** | no recycling |
| Target metadata/read lengths | Target full | Target full | **No** | Target isolation |

如果Draft metadata中某个mutable tensor storage与真实Target metadata alias，rescue会从
canonical source值创建Draft-owned clone，再由P3 store验证disjointness。该动作不改变
slot/position值或Target owner/content；它只满足Draft/Target lifetime isolation。

## 8. Epoch / Validate / Workspace / Lease

### 8.1 Epoch provenance

```text
scheduler ordered req_ids
  -> req_id_to_index
  -> idx_mapping_np
  -> AscendInputBatch(req_ids, idx_mapping_np, idx_mapping)
  -> one outer DFlash/DSpark propose
  -> DraftWindowProposalEpochSource.begin()
```

epoch不能由外部随意传值。每个real outer proposal严格+1；同proposal内重复validate不增代。
context冻结：

- input batch Python identity（仅作“同一proposal对象”检查，不替代epoch）；
- ordered stable request IDs；
- active CPU mapping contents。

materialize前后都核验context，随后P3 identity/lease/workspace/typed inputs/store继续携带同一
`mapping_epoch`。reorder、finish/add、same-row replacement、same-pointer in-place rewrite
和ABA stale handle都有回归。

### 8.2 Single validation boundary

唯一正式边界：

```text
DraftMetadataInputs
  -> _validated_draft_attention_read_inputs(inputs, expected_identity)
  -> inputs.validate_for(expected_identity)
  -> AscendDraftAttentionReadInputs
  -> builder
```

spy测试确认builder之前正好一次；stale identity无法到达builder。

### 8.3 Workspace and lease

- single speculator-owned fixed-capacity workspace；
- no alias canonical FullSource；
- active/tail先全量zero再写；
- Window exact由CPU同源plan写入device fixed backing；
- one serialized lane；
- pressure deterministic error，不覆盖active；
- outer proposal是唯一retirement/exception owner；
- eager同stream在`super().propose()`返回后retire；
-没有fake event进入production，也不声称真实Async-safe。

真实NPU stream/completion时序仍属于runtime Gate。

## 9. Profile / Dummy Behavior — C-01

### Before rescue

归档prototype：

```python
if dummy_run or is_profile:
    raise NotImplementedError(...)
```

在临时prototype worktree执行新regression：

```text
1 failed
NotImplementedError:
MRV2 draft-window P4a is not enabled for dummy/profile proposals
```

这会使合法Window配置在engine profile/startup阶段失败。

### After rescue

dummy/profile scope使用instance-local `_draft_window_bypass_active`：

- 不调用epoch `begin()`；
- 不materialize workspace；
- 不创建live typed inputs；
- 不publish Draft Window metadata；
- `_build_draft_attn_metadata()` exact-super到baseline；
-退出时只清bypass flag，不执行“必须consume Window”的production检查。

当前参数化regression结果：`3 passed`；`_next_epoch == 0`、workspace/store均为空。

## 10. Target Isolation — M-01

Window ON进入materialize或builder前调用
`_require_nonempty_target_metadata()`：

- 必须是非空`Mapping`；
-必须直接来自`self.model_state.attn_metadata`；
- `None`、`{}`或临时fake Target均hard fail；
- builder返回后再次验证Target top-level owner identity未被替换；
- `_isolate_draft_metadata_from_target()`处理nested object/list/dict/dataclass/slots与
  Tensor storage alias；
- `DraftMetadataStore.publish(..., target_metadata=target_metadata)`再次验证mutable
  storage disjointness。

tests覆盖Target top-level identity/content、nested list/dict/Tensor storage、shared mutable
dataclass和builder中owner replacement。Target没有被Draft过滤、改写或替换。

## 11. DFlash

支持条件为single executable dense-GQA group、serialized eager、graph NONE、async false、
TP/DP/PP/PCP/DCP=1、无SP/DSA-CP/FlashComm、prefix cache OFF、decode-only。

timing：

```text
full prepare_dflash_inputs
 -> full positions/query/slot mapping
 -> context KV write
 -> proposal epoch
 -> P1/P2/P3 Window read plane
 -> local Ascend metadata assembly
 -> Draft forward
 -> retire
```

DFlash真实`num_query_per_req = K + 1`；Window scalar
`future_offset=0`。apply-time CPU upper只使用该真实width一次，不在builder二次加step。

## 12. DSpark

只支持非DeepSeek-V4/V4.1 co-trained、且P2实际inventory为single dense-GQA的eligible
DSpark。

| DSpark config | Real query width |
|---|---:|
| default `sample_from_anchor=True` | `K` |
| explicit `sample_from_anchor=False` | `K+1` |
| DFlash comparison | `K+1` |

rescue读取speculator当前`num_query_per_req`，不按method名称猜测。现有
`build_draft_attn_metadata_factory()`继续透传positions/is_prefilling；新增真实wrapper
test证明Window exact/upper kwargs和该注入同时存在。

DeepSeek-V4 family DSpark仍：

```text
warning once -> forced OFF -> zero P2/P3/P4 Window state
```

Target SFA/DSA不等于Draft backend；只有P2实际consumer inventory决定资格。

## 13. Window OFF Parity

OFF没有`_draft_window_runtime_state`，mixin立刻调用exact
`super()._build_draft_attn_metadata(...)`。没有vendor-local OFF assembly。

differential test对同一harness分别直接调用upstream DFlash path和Ascend mixin OFF path，
比较：

- kwargs key set；
- block-table storage/content；
- device seq-length storage/content；
- CPU upper；
- max seq/query；
- slot-mapping storage/content；
- positions与is_prefilling storage/content；
- query-start GPU/CPU；
- causal与kv-cache config。

所有比较通过。optional `seq_lens_cpu=None`仍保持Ascend builder baseline behavior，
`seq_lens_cpu_is_explicit=False`。

## 14. Fail-closed Matrix

| Route / feature | Behavior before workspace/materialize/forward |
|---|---|
| CONFIG OFF | exact baseline；zero P2/P3/P4 state |
| MTP | warning once + forced OFF |
| DeepSeek-V4/V4.1 co-trained DSpark | warning once + forced OFF |
| plain Eagle / unknown method / dynamic K | explicit P1 rejection |
| Eagle3 | P4b；not enabled here |
| DFlash2 | inventory-only；no P4 runtime state |
| multi-group / mixed consumer | reject |
| MLA / DSA / SFA / V4.1 / native/recycling / unknown layout | reject |
| Graph FULL / FULL_DECODE_ONLY / PIECEWISE | reject |
| async | reject |
| TP/DP/PP/PCP/DCP > 1 | reject |
| SP / DSA-CP / FlashComm | reject |
| prefix cache ON | reject before source/workspace |
| terminal pure prefill（本step完成全部prompt） | explicit baseline-full bypass；不发epoch、不创建Window state |
| mixed prefill/decode | reject before epoch/materialize |
| continuing chunked/function prefill | reject before epoch/materialize |
| source shortage / stale epoch / active lane pressure | deterministic hard fail |
| dummy/profile | baseline bypass；not a production Window generation |

不得通过静默关闭用户的其他feature继续Window ON。

## 15. CPU / Static Tests

测试环境：

```text
VLLM_VERSION=0.29.0
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm
vLLM HEAD=84030bbe3d74d99bad477a3d2e37a973ccd8865c
```

| Command / scope | Result | Meaning / limitation |
|---|---|---|
| archived C-01 regression | `1 failed` | 精确复现旧profile/dummy blocker |
| current C-01 `-k profile_and_dummy` | `3 passed` | no epoch/workspace/store；CPU |
| `test_draft_window_eager.py` | `40 passed` | epoch, seam, ON/OFF, prefill boundary, Target, C-01；CPU |
| P1/P2/P3/P4a + DFlash2/DSpark + BlockTables + attn | `328 passed, 2 subtests passed` | no NPU |
| `tests/ut/spec_decode --ignore=...vwn...` | `439 passed, 13 skipped, 2 subtests passed` | locally runnable suite |
| full `tests/ut/spec_decode` | `441 passed, 13 skipped, 7 failed, 2 subtests passed` | 7个既有VWN host failures；不是PASS |
| Ruff check | PASS | 12 changed files |
| Ruff format check | PASS | 12 changed files |
| targeted Mypy | PASS | 7 production files；follow-imports skip |
| compileall | PASS | changed files |
| `git diff --check` | PASS | staged C4 |
| selected repository hooks | PASS | codespell、typos、filename、package、logger、imports、boolean-with、long-function、symbolic-meta |
| full `format.sh ci` | environment-blocked | markdownlint install `npm EALLOWGIT`；不写PASS |

主要命令：

```bash
VLLM_VERSION=0.29.0 \
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
.venv/bin/pytest -q tests/ut/spec_decode/test_draft_window_eager.py

VLLM_VERSION=0.29.0 \
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
.venv/bin/pytest -q \
  tests/ut/spec_decode/test_draft_window.py \
  tests/ut/spec_decode/test_draft_window_runtime.py \
  tests/ut/spec_decode/test_draft_window_eager.py \
  tests/ut/spec_decode/test_dflash2_v2.py \
  tests/ut/spec_decode/test_dspark_speculator.py \
  tests/ut/worker/test_extract_hidden_states_speculator_v2.py \
  tests/ut/worker/v2/test_v2_block_table.py \
  tests/ut/worker/test_attn_utils_v2.py \
  tests/ut/attention/test_attention_v1.py
```

full suite的7个失败全部在
`tests/ut/spec_decode/test_speculators_vwn_eagle3.py`，共同stack终止于upstream selector
`ValueError: Invalid attention backend for None`，未进入本功能文件，与P1/P2/P3记录一致。

关键tests：

- same Tensor pointer in-place mapping rewrite；
- request reorder、finish/add、same-row replacement；
- stale proposal无法到builder；
- source shortage；
- short/boundary/non-boundary/long scalar plan；
- single validate spy；
- no production P3 debug `.cpu()` validator；
- full table/slot/positions/Target unchanged；
- explicit CPU exact default parity；
- wrapper/factory positions passthrough；
- upstream drift guard；
- C-01 red/green；
- M-01 None/empty/replaced owner。

## 16. Upstream Baseline Compatibility Tests

硬性兼容证据：

1. active vLLM HEAD精确为
   `84030bbe3d74d99bad477a3d2e37a973ccd8865c`；
2. `git status --porcelain`为空；
3. vLLM不存在`DraftAttentionReadInputs`；
4. vLLM-Ascend没有conditional import/fallback到prototype API；
5. P1/P2/P3/P4a tests均在该checkout运行；
6. OFF differential path exact-super；
7. normalized AST/signature guard固定本地assembly依赖的upstream contract；
8. production diff只存在于vLLM-Ascend C4。

因此公司服务器只需原始固定vLLM baseline与该vLLM-Ascend commit。

## 17. NPU Test Plan

`G-GQA-EAGER`只能由公司NPU Agent关闭。固定：

- single card；
- TP=DP=PP=PCP=DCP=1；
- one executable dense-GQA gid；
- serialized eager；
- graph NONE；
- async/prefix/prefill/parallel extensions OFF；
-相同model、prompt、seed、scheduler与sampling config；
- A=Window OFF，B=Window ON。

### Case matrix

| ID | Route | Context | Purpose |
|---|---|---|---|
| N01 | DFlash `K+1` | `L <= W` | short context equals full visibility |
| N02 | DFlash `K+1` | exact block boundary | anchor/column boundary |
| N03 | DFlash `K+1` | non-boundary | visible length and capacity slack |
| N04 | DFlash `K+1` | long `L > W` | physical eviction/read set |
| N05 | DSpark default `K` | boundary + long | method-specific width |
| N06 | DSpark explicit false `K+1` | boundary + long | alternate width |
| N07 | batch reorder | A/B -> B/A | mapping freshness |
| N08 | finish/add | B/A -> C/A | generation + row mapping |
| N09 | same-row replacement | row17 A -> D | request identity |
| N10 | long repeated proposals | pressure/reuse | workspace/lease lifecycle |
| N11 | profile/startup | legal Window config | C-01 startup |
| N12 | unsupported matrix samples | graph/async/prefix/prefill/TP2 | fail closed before Window state |

每case记录：

- commits/model/config/seed/command；
- CPU expected visible token set；
- P1 plan与P2 descriptor；
- materialized Window table、active columns和lengths；
- canonical full table snapshot；
- slot mapping、positions、query start；
- actual Draft Attention physical operand/read set；
- Draft proposal/logits（可获取时）；
- Target metadata identity/content、read lengths、logits；
- final output；
- stream/event ordering；
- D2H/H2D trace与kernel profiler。

通过标准：

- B physical Draft read set等于CPU oracle；
- A保持baseline；
- write/slot/query/Target invariants A==B；
- stale/row replacement无串请求；
- next generation不在reader完成前覆盖；
- profiler无未批准的额外hot D2H；
- unsupported combinations显式拒绝。

## 18. D2H / Performance Gate — M-02

静态计数：

| Path | Device -> host length operation |
|---|---:|
| baseline parallel-drafting | builder对device exact生成host list：1 |
| feature | prepared full-exact controlled snapshot：1 |
| feature builder | 使用CPU exact list：0 device read |
| P3 production validator | debug exact `.cpu()`与device tail reduction：0 |
| feature net increase | **0（静态源码计数）** |

另外有CPU->device fixed-workspace copy和Window table device copy；它们不是D2H，但仍须纳入
NPU profiler。CPU tests不能证明真实NPU同步、overlap或吞吐，因此性能Gate仍OPEN。

## 19. Remaining Gates

| Gate | Status / owner |
|---|---|
| independent P4a review | OPEN；DeepSeek review + Codex adjudication |
| `G-GQA-EAGER` | OPEN；company NPU physical-read/lifecycle/profiler |
| Target logits/output invariant | OPEN on NPU |
| real completion timing | OPEN on NPU；serialized same-stream only |
| P4b `G-AR-STEP` | NOT STARTED |
| Graph capture/replay | BLOCKED |
| Async multi-lane | BLOCKED |
| prefix cache / mixed/function prefill | BLOCKED |
| TP/DP/PP/PCP/DCP/SP/DSA-CP/FlashComm | BLOCKED |
| MLA/DSA/SFA/native/recycling/multi-group/DFlash2 | BLOCKED |
| delivery manifest / release | HOLD |

## 20. Developer Reading Guide

1. `worker/v2/spec_decode/draft_window_eager.py:85`：production epoch source。
2. 同文件`:237`：outer proposal scope与C-01 bypass。
3. 同文件`:297`：P1/P2/P3 materialization。
4. 同文件`:356`：single validate boundary。
5. 同文件`:378`：OFF exact-super与Window ON入口。
6. 同文件`:446`：唯一vendor-local metadata assembly。
7. 同文件`:513`：existing Ascend builder adapter。
8. 同文件`:526,556`：real Target要求与nested isolation。
9. `dflash/speculator.py:34,150`与
   `dspark/speculator.py:50,199`：MRO和proposal接入。
10. `draft_window.py:211,1087,1336,1807,1850`：FullSource、CPU valid counts、
    workspace、store、runtime。
11. `worker/v2/attn_utils.py:223`：optional CPU exact seam。
12. `attention/attention_v1.py:339-411`：explicit CPU exact consumer。
13. `tests/ut/spec_decode/test_draft_window_eager.py`：先读drift/OFF/C-01/M-01 tests，
    再读epoch/lifecycle tests。

## 21. Mental Model

1. vLLM完全不变；所有production owner都在Ascend speculator instance。
2. OFF、profile/dummy以及“本step完成全部prompt”的纯prefill直接走upstream baseline；
   mixed或continuing chunked prefill仍fail closed。
3. Window只替换Draft read table和read lengths。
4. full slot mapping、positions、query layout、KV write和Target始终不变。
5. 每个real proposal只有一个caller-owned monotonic epoch。
6. P3 workspace tensor是borrowed view；builder前必须走唯一validate boundary。
7. local assembly只复制upstream builder kwargs seam，不复制proposal/forward。
8. existing module wrapper只选Ascend builder，不承载Window state。
9. C4只证明CPU/static contract；NPU physical read才证明feature runtime correctness。
10. P4b、Graph、Async和复杂backend没有被顺带开启。

# Ascend-only Independent Review Resolution

### 22.1 Review metadata

| Item | Value |
|---|---|
| Independent review | DeepSeek `P4a Ascend-only Rescue — 独立 Review` |
| reviewed C4 | `0dd83e9f75d4b2d766126af3a7f92352e342f756` |
| review-fix | `4c1f69146915f4f0ae5a6a61371ebfe181237d8f` |
| adjudication time | 2026-10-10 16:34:39 +0800 |
| vLLM evidence | HEAD `84030bbe3d74d99bad477a3d2e37a973ccd8865c`；status/diff empty |
| architecture escalation | **NONE** |

### 22.2 Finding statistics

按review中的5条新finding、3条previous-finding复核项和1条architecture-escalation
主张统计：

| Resolution | Count |
|---|---:|
| ACCEPTED | 5 |
| PARTIALLY_ACCEPTED | 1 |
| REJECTED | 1 |
| NEEDS_NPU_VERIFICATION | 1 |
| OPTIONAL_STYLE_ONLY | 1 |
| ARCHITECTURE_ESCALATION | 0 |

### 22.3 Resolution table

| ID | Severity | Finding / claim | Resolution | Evidence | Code / test / doc change |
|---|---|---|---|---|---|
| C-02 | Critical | `has_prefill`在真实proposal入口直接抛错，使普通请求首个prefill step不可达decode | **ACCEPTED** | baseline `model_runner.py:2040-2065`每step无条件调用speculator；`InputBatch`提供computed/scheduled/prefill length，可区分terminal、mixed和continuing chunk | 先用旧代码复现red；新增terminal pure-prefill baseline bypass，随后decode正常Window；mixed与continuing chunked仍在epoch/workspace前拒绝 |
| F-02 | Major | vendor-local assembly只有AST/signature guard，没有与upstream assembly的正向等价测试；非均匀分支当前不可达 | **ACCEPTED** | DFlash/DSpark真实call不传`query_start_loc_np`；旧代码的非均匀分支red test未抛错 | 新增full-equivalent read differential，比较query/slot/positions/causal/kv fields；非均匀layout显式fail closed |
| F-03 | Minor | Target alias两层遍历漏掉NumPy/buffer alias，并建议合并遍历 | **PARTIALLY_ACCEPTED** | 两条旧代码red test证明NumPy view既未clone也未被Store拒绝；但Draft-side修复与Store-side最终审计是两个独立信任边界 | 两层均增加NumPy storage/view检测；保留两层职责，不合并成单点检查 |
| F-04 | Minor | `references_persistent_num_blocks`实际表示rotating GPU current view，命名误导 | **ACCEPTED** | C4将stable owner迁到CPU，但旧方法名未同步 | 重命名为`references_current_num_blocks_gpu_view`；新增GPU view轮换与CPU stable owner test |
| F-05 | Style | 缺少“无global/ContextVar transport”的静态断言 | **OPTIONAL_STYLE_ONLY** | 人工grep成立，但原测试未固化 | 新增AST test，禁止`global`statement与`ContextVar`符号 |
| C-01 | Critical（previous） | eligible profile/dummy blocker已关闭 | **ACCEPTED** | 参数化`(dummy,profile)`三例均走baseline；epoch=0，无context/live inputs/workspace/store | 无production变化；最终复跑3 passed |
| M-01 | Major（previous） | None/empty Target及owner replacement已关闭 | **ACCEPTED** | production在materialize/builder前要求真实非空`model_state.attn_metadata`；replacement在publish前失败 | 无production变化；None/empty与owner replacement regression继续通过 |
| M-02 | Major（performance） | hot path D2H需真实profiler | **NEEDS_NPU_VERIFICATION** | CPU/static只能证明feature路径一次controlled snapshot并替代baseline builder read，不能证明NPU sync/H2D成本 | 不增加额外host/device校验；保留NPU profiler Gate |
| A-01 | Architecture | 必须由owner在“所有prefill baseline bypass”和“windowed prefill”二选一，否则architecture escalation | **REJECTED** | `InputBatch`的ordered per-row prefill状态、computed、scheduled和prefill length允许第三种可证明分类；decode-only Frozen scope不要求打开windowed prefill | terminal pure-prefill baseline bypass；mixed/continuing chunked继续fail closed；不修改Final Design Frozen架构 |

DeepSeek提出的“prefill全部bypass”与“windowed prefill”不是唯一两种选择。当前源码有足够字段形成更窄且与Frozen scope一致的第三种契约：

```text
all rows prefilling
+ computed_prefill + scheduled >= prefill_len for every row
    -> terminal pure-prefill baseline bypass

mixed prefill/decode
or any row remains prefilling after this step
    -> fail closed before epoch/workspace
```

因此C-02不需要修改Final Design架构，也不打开`G-PREFILL`；P4a仍是decode Window。

### 22.4 Final design seam and OFF parity

最终seam仍是方案C，属于 **ACCEPTED TRADEOFF UNDER ASCEND-ONLY CONSTRAINT**：

- OFF、profile/dummy、terminal pure-prefill exact-super到原版vLLM；
- decode Window只在instance-owned mixin中组装read kwargs；
- full slot mapping、positions、query layout和Target不被transport覆盖；
- 无module-global Window state、无ContextVar、无shared-owner swap；
- 正向differential证明full-equivalent vendor assembly除显式`seq_lens_cpu`外与upstream一致；
- AST/signature drift guard继续钉住依赖的upstream contract。

### 22.5 Red-to-green evidence

review-fix前新增的5个聚焦测试在C4上结果为`5 failed`：

1. terminal pure-prefill抛`NotImplementedError`；
2. nonuniform dead branch未fail closed；
3. Draft-side NumPy view仍alias Target；
4. Store接受NumPy shared storage；
5. GPU current-view新语义没有准确API。

同组修复后为`10 passed`；完整P4a eager为`40 passed`。

### 22.6 Final tests

| Command / scope | Result | Limitation |
|---|---|---|
| C-02/F-02/F-03/F-04/F-05 focused | `10 passed` | CPU/state-machine evidence |
| C-01 eligible profile/dummy | `3 passed` | CPU eligible runtime harness；非NPU startup |
| M-01 None/empty/owner replacement | PASS | CPU production-boundary regression |
| `test_draft_window_eager.py` | `40 passed` | no NPU attention kernel |
| P1/P2/P3/P4a + DFlash/DSpark/DFlash2 + BlockTables/attn | `328 passed, 2 subtests passed` | CPU/static |
| locally runnable `tests/ut/spec_decode` | `439 passed, 13 skipped, 2 subtests passed` | VWN host file excluded |
| full `tests/ut/spec_decode` | `441 passed, 13 skipped, 7 failed, 2 subtests passed` | 7个既有`Invalid attention backend for None`；不是PASS |
| Ruff check / format | PASS | final 10-file P4a/static scope |
| targeted Mypy | PASS | 7 production files；`--follow-imports=skip` |
| compileall / `git diff --check` | PASS | final changed scope |
| selected executable hooks | PASS | codespell、typos、filename、package、logger、forbidden-import、boolean-context、long-function、symbolic-meta、suggestion |

### 22.7 Final invariant audit

| Invariant | Final status |
|---|---|
| vLLM exact baseline / no prototype API dependency | PASS |
| production changes only in vllm-ascend | PASS |
| OFF exact-super parity | PASS |
| terminal pure-prefill creates no epoch/workspace/store | PASS |
| mixed/continuing chunked prefill fail before Window state | PASS |
| stale input cannot bypass single validation boundary | PASS |
| slot mapping / positions / query / canonical full table unchanged | PASS |
| Target nonempty owner + Tensor/NumPy nested storage isolation | PASS |
| no global / ContextVar / shared owner swap | PASS |
| C4 vendor assembly has positive differential + drift guard | PASS |
| Graph / Async / P4b / complex backend not enabled | PASS |
| NPU physical read-set and performance proven | **NO — Gate OPEN** |

### 22.8 Final gates

| Gate | Status |
|---|---|
| `R-REPO-01` | **SATISFIED** |
| `G-ASCEND-ONLY-INTEGRATION` | **STATIC CLOSED** |
| P4a CPU/static contract | **PASS** |
| `G-GQA-EAGER` | **OPEN — NPU REQUIRED** |
| `G-PREFILL` | **OPEN**；只有terminal pure-prefill baseline bypass，不是Window prefill支持 |
| P4b / `G-AR-STEP` | **NOT STARTED / OPEN** |
| Graph / Async / prefix / parallel / complex backend | **BLOCKED per route** |
| Feature release | **HOLD** |

`P4a ASCEND-ONLY STATIC FINAL: PASS`

`G-GQA-EAGER: OPEN — NPU REQUIRED`

`P4b NOT STARTED`
