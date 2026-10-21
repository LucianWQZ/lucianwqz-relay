# P4b Eagle3 Static-K Eager Integration Implementation Notes

## Document Status

| Item | Value |
|---|---|
| Final Design | `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md` |
| Implementation Plan | `MRV2_Draft_Window_Implementation_Plan.md` |
| Repository rule | `R-REPO-01: production may modify vllm-ascend only` |
| exact vLLM baseline | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM checkout | exact HEAD；working tree clean；baseline diff empty |
| P4a Final parent | `4c1f69146915f4f0ae5a6a61371ebfe181237d8f` |
| P4b / C5 | `d0c8883816f0e1fe333dc9f3197d3c4e47c475a5` |
| C5 title | `feat(spec-decode): integrate MRV2 draft windows for Eagle3 eager` |
| C5 parent | exact P4a Final `4c1f69146915f4f0ae5a6a61371ebfe181237d8f` |
| review-fix | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` |
| review-fix title | `fix(spec-decode): address P4b Eagle3 window review findings` |
| CPU/static status | **STATIC FINAL: PASS** |
| NPU status | **NOT RUN** |
| `G-AR-STEP` | **OPEN — NPU REQUIRED** |
| P4a `G-GQA-EAGER` | **OPEN — NPU REQUIRED**，状态未被P4b改变 |
| Graph / Async / complex backend | **BLOCKED / fail closed** |
| Feature release | **HOLD** |
| document time | 2026-10-11 14:06:33 +0800（Asia/Shanghai） |

本文件已包含DeepSeek独立Review与Codex事实裁决。C5加review-fix建立了Eagle3 static-K
serialized eager的CPU/static correctness contract。没有真实NPU physical read-set、stream
timing或性能证据，因此不能写runtime `P4b FINAL PASS`，也不能关闭`G-AR-STEP`的NPU Gate。

## 1. P4b解决什么

P4a面向DFlash和eligible DSpark：一次proposal准备一组并行Draft query，并只需要一次
Window read view。P4b面向Eagle3 autoregressive drafting：同一个proposal先执行一次first
pass，再执行`K-1`个单token AR step；每一步的full exact end、slot mapping和metadata都可能
变化。

P4b解决以下问题：

1. 从真实proposal入口冻结未扣rejection的`L0`。
2. 使用真正配置的static `K`计算`H=L0+K`与proposal-frozen `S`。
3. Window ON first pass不再直接复用Target metadata，而是构建Draft-private metadata。
4. 每个后续AR step使用真实`E_s`，保持同一个`S`，并从canonical FullSource重新刷新。
5. 复用P3 owner/lease/store，同时增加“同一proposal epoch内严格step continuation”的最小协议。
6. 保持absolute positions、query layout、full physical slot mapping、Target metadata和canonical
   FullSource不变。

P4b不解决：plain Eagle、MTP、dynamic K、DFlash2、Graph、Async、multi-group、MLA、DSA、
SFA、V4.1、recycling、parallel topology、prefix cache、mixed prefill/decode、Window化的
chunked prefill和真实NPU correctness。所有pure scheduler-prefill chunk显式走baseline full
read，且不创建Window state；这不等于关闭`G-PREFILL`。

## 2. Source Preflight

### 2.1 Class / MRO

原版vLLM：

```text
DraftModelSpeculator
  └─ AutoRegressiveSpeculator
       ├─ propose
       ├─ _prefill
       ├─ _multi_step_decode
       ├─ _build_draft_attn_metadata
       └─ _generate_draft
```

Ascend最终MRO：

```text
AscendAutoRegressiveSpeculator
  ├─ Eagle3DraftWindowMixin          # only proposal/step Window ownership
  └─ upstream AutoRegressiveSpeculator
```

`Eagle3DraftWindowMixin`没有复制proposal、model forward、sampling、position更新或slot kernel。
Window OFF以及没有P1 eligible policy的plain Eagle/MTP仍走原Ascend/upstream路径。

### 2.2 Exact upstream anchors

| Source | Current fact |
|---|---|
| `vllm/v1/worker/gpu/spec_decode/speculator.py:88-96` | `DraftModelSpeculator.__init__`把`num_speculative_steps`直接设为configured `num_speculative_tokens` |
| `autoregressive/speculator.py:204` | `propose()`是一个真实proposal边界 |
| `:263` / `:758` | `prepare_prefill_inputs()`在first pass前准备Draft full state |
| `:328` / `:798-852` | `prepare_decode_inputs()`在first pass后扣除`num_rejected`并形成step 1 full state |
| `:440` | baseline first pass直接复用传入的Target metadata和slot mappings |
| `:484` | non-fused `_multi_step_decode()`每step先算full slot，再build metadata，再forward |
| `:625` / `:881-952` | `_generate_draft()`后由`update_draft_inputs()`为下一步递增positions与seq lengths |

测试`test_eagle3_upstream_drift_guard_pins_proposal_and_step_contracts`固定了上述构造器、
proposal、first-pass、multi-step、forward、三个prepare/update launcher，以及真正定义
`E_s`语义的`_prepare_prefill_inputs_kernel`、`_prepare_decode_inputs_kernel`和
`_update_draft_inputs_kernel`的AST hash与proposal signature。未来upstream drift会使测试
显式失败。

### 2.3 Real eager call chain

```text
AscendAutoRegressiveSpeculator.propose
  → upstream prepare_prefill_inputs
  → _prefill                                # proposal step 0
  → upstream prepare_decode_inputs          # applies rejection correction
  → Ascend _multi_step_decode
       → snapshot actual step-1 exact once
       → upstream non-fused step loop
           → compute full positions/query/slot mapping
           → Ascend _build_draft_attn_metadata
           → upstream _generate_draft
           → upstream update_draft_inputs
```

P4b materialize点均晚于对应step的full position/slot稳定点。

## 3. L0 / K / H / S

| Field | Producer | Consumer | Lifetime | Contract |
|---|---|---|---|---|
| `L0` | proposal-entry `input_batch.seq_lens_np` | frozen proposal planner | one proposal | Target prepared full exact；在`prepare_decode_inputs`扣rejection前复制 |
| `K` | upstream `num_speculative_steps == speculative_config.num_speculative_tokens` | P2 provider + P4b planner | speculator config | static only；dynamic speculative decoding在speculator创建前fail closed |
| `H` | `L0 + K` | frozen scalar plan | one proposal | full proposal horizon |
| `S` | `B * floor(max(H-W, 0)/B)` | every first/AR step | one proposal | proposal-frozen，禁止每step重算 |
| `E_0` | `L0` | first-pass descriptor | step 0 | first-pass actual full end |
| `E_1` | post-`prepare_decode_inputs` Draft `seq_lens` | decode snapshot | proposal steps 1.. | 已应用rejection并按Eagle3语义advance一次 |
| `E_s` | `clamp(E_1 + (s-1))` | step planner | one step | 由upstream每成功forward后递增的静态语义推导 |
| `V_s` | `E_s-S` | metadata lengths | one step | 先要求`S<=E_s<=H`；exact可达`W+B-1`，不clamp到`W` |

`build_eagle3_frozen_proposal_plan()`创建immutable `Eagle3FrozenProposalPlan`；
`build_eagle3_step_materialization_plan()`只接受真实`E_s`并验证
`S <= E_s <= H`，不会调用可重算anchor的P2 one-shot路径。

## 4. First-pass baseline behavior

原版`AutoRegressiveSpeculator.propose()`在eager first pass中把Target的：

- `attn_metadata`；
- per-layer `slot_mappings`；
- query layout和positions；

直接传给Draft `_prefill()`。这是Window OFF的合法baseline，也继续保持不变。

Window OFF没有P4b proposal context，因此Ascend `_prefill()`继续执行原有Target-only layer过滤，
随后exact `super()._prefill(...)`。plain Eagle、MTP、profile/dummy和任何pure scheduler-
prefill chunk的baseline bypass都不会创建P4b generation。

## 5. Window ON first-pass

Window ON的step 0执行：

```text
Target prepared full state
  → copy CPU L0 (no feature D2H)
  → freeze H/S
  → gather canonical valid counts using idx_mapping
  → P2 frozen-step descriptor
  → P3 materialize phase=PROPOSAL, step=0
  → DraftMetadataInputs.validate_for(identity)
  → Ascend vendor-local metadata builder kwargs
  → isolate from real Target metadata
  → DraftMetadataStore.publish(real Target owner)
  → Draft forward with original full slot_mappings argument
  → retire generation
```

`_build_eagle3_private_attn_metadata()`只改变Draft read carrier：Window block tables、Window
device/CPU exact、CPU upper和max read length。它保留first-pass query-start GPU/CPU、实际与
padded token/request geometry、positions factory、causal、KV config和full slot owner。

Target metadata必须是`model_state.attn_metadata`中的真实非空owner。builder返回值在任何
`attn_state`写入之前先经过nested Tensor/NumPy storage isolation；然后才从对应Target layer
复制first-pass state。Draft metadata发布到P3 DraftMetadataStore，Target对象不被替换。

## 6. Proposal-frozen Anchor

例：

```text
B = 16
W = 64
K = 3
L0 = 100
H = 103
S = 16 * floor((103 - 64) / 16) = 32
```

假设rejection后真实step ends为：

```text
step 0: E0 = 100, V0 = 68
step 1: E1 = 98,  V1 = 66
step 2: E2 = 99,  V2 = 67
```

则：

```text
S0 = S1 = S2 = 32
```

测试同时覆盖：

- short context：`L0=60, H=63 <= W`，`S=0`；
- exact anchor boundary：`L0=93, H-W=32`，`S=32`；
- non-boundary：`L0=94, H-W=33`，仍floor到`S=32`。

## 7. Per-step E_s

Step 0使用CPU `input_batch.seq_lens_np`，不做device-to-host snapshot。

Step 1发生在upstream `prepare_decode_inputs()`之后。该kernel执行：

```text
seq_len = target_seq_len - num_rejected
if advance_draft_positions:
    seq_len = min(seq_len + 1, max_model_len)
```

P4b在`_multi_step_decode()`入口对这个真实device state做一次受控D2H，得到`E1`。后续
step不再次D2H；因为static Eagle3的upstream `update_draft_inputs()`在非final step后恰好
`+1`，所以host侧使用：

```text
E_s = clamp(E1 + (s - 1), max_model_len), s >= 1
```

每一步仍通过proposal epoch fingerprint、request count、source identity、step顺序和P2
descriptor验证。该静态推导依赖已pin的upstream AST；真实NPU同步成本仍由profiler验证。

## 8. Future Block

关键例子：

```text
B=16, W=64, K=3, L0=64
H=67, S=0
```

Step 0 history恰好结束在第4个block边界；后续AR step会进入第5个physical column。实现没有
保留step 0的narrow column count作为下一步source，而是：

1. step 0从FullSource取4列；
2. retire step 0；
3. step 1重新bind相同canonical FullSource；
4. 用新的`E1=65` descriptor取5列，包括future/current physical column。

CPU oracle测试在step 0后故意把整个Window workspace写成`-99`，step 1仍与canonical full
table前5列完全一致，证明不存在stale clone、missing future column或window-of-window。

## 9. Rejection

`L0`在first pass前冻结，rejection correction在first pass后由upstream
`prepare_decode_inputs()`应用，因此：

- 当前proposal的`S`不因rejection重算；
- `E1`可小于`L0`；
- 后续`E_s`从rejection-corrected `E1`继续增长；
- 若rejection使`E_s < S`，Frozen invariant被破坏，当前proposal显式fail closed；
- 下一个真实proposal获得新epoch、新`L0`并重新计算新`S`。

测试覆盖同一block内变化、跨block rejection、跨越frozen anchor的拒绝以及next proposal
recompute。这里的运行期中止是Final Design I24、§9.3与T04明确要求的correctness guard，
不是P4b遗漏：`W>=K`只保证proposal-entry初始几何，不承诺任意rejection后的`E_s>=S`。
不能把该情形改成`V_s=0`，也不能用会拒绝其它安全residue的全局更强gate替代逐step断言。

## 10. FullSource refresh

每个step调用P3 continuation materialize，但`DraftWindowRuntimeState`仍执行：

```text
capability.full_source.bind_batch(idx_mapping)
  → validate same source identity
  → workspace.materialize(full_source=bound_source, descriptors=current step)
```

上一step的`window_block_table`只是一段可复用backing，不是source。`describe_frozen_step()`
只是把proposal-frozen absolute interval投影到canonical source columns；它不会对上一Window
再次切片。

## 11. Read vs Write

| State | Window OFF | Window ON | Changed? |
|---|---|---|---|
| Draft read block table | canonical full | step Window view | **Yes — read only** |
| Draft device exact length | full exact | `V_s` | **Yes — read only** |
| Draft CPU exact / upper | full | Window exact / bounded upper | **Yes — read only** |
| Draft max read length | full max | Window max | **Yes — read only** |
| physical slot mapping | full canonical | same full canonical | No |
| absolute positions | baseline full | same values/semantics | No |
| query start/layout | baseline | same values/semantics | No |
| canonical FullSource table | owner | same owner/content | No |
| physical KV allocation/write | baseline | baseline | No |
| Target metadata / lengths | Target full | same Target owner/content | No |
| Target logits/output | baseline | intended identical | Not statically proven；NPU gate |

FIA实际read-length carrier使用`cpu_window_exact`，不是planning upper。原因是P4b给Ascend
builder同时提供device exact、CPU exact和CPU upper；`AscendAttentionMetadataBuilder`在
`_seq_lens_cpu is None`时从显式CPU exact构造`seq_lens`、`seq_lens_cpu`与`seq_lens_list`。
`cpu_window_upper`只用于容量/tiling校验。upstream eager AR loop又会在每个step forward前重建
metadata，因此baseline `_generate_draft()`之后的`_update_decode_attn_metadata()` mutation不会
成为下一step forward的输入。把upper作为FIA exact会违反Final Design §9.6。

## 12. Target isolation

```text
Target ModelState
  └─ model_state.attn_metadata  (Target-owned, full)

AscendAutoRegressiveSpeculator
  └─ DraftMetadataStore
       └─ independent Eagle3 step metadata (Window read carrier)
```

保护顺序：

1. 在materialize前要求real Target非None、非空Mapping。
2. 要求first-pass传入对象与`model_state.attn_metadata`同一owner。
3. builder完成后再次检查Target owner未变化。
4. 在写per-layer `attn_state`之前隔离top-level、nested object、Tensor storage和NumPy shared
   memory。
5. `DraftMetadataStore.publish()`再次审计Draft与Target mutable storage不alias。
6. forward只接受从当前generation store读出的同一Draft object。
7. retire/reset后entry不可读。

测试特意让builder返回Target-owned layer和nested Tensor/NumPy alias，验证Draft被clone且
Target identity/content/storage不变。

## 13. P3 lifetime如何被P4b使用

### 13.1 Proposal identity vs step identity

一个proposal只创建一个caller-owned `mapping_epoch`；step 0/1/2共享该epoch，但拥有不同的
monotonic `generation_id`与严格递增`step`：

```text
proposal epoch = 10
  generation 40: phase=PROPOSAL, step=0
  generation 41: phase=STEP,     step=1
  generation 42: phase=STEP,     step=2
```

`materialize()`仍保持P3原contract：新proposal的epoch必须严格增加。P4b新增唯一受限API
`materialize_serialized_step()`，它只允许normalized Eagle3在以下全部条件成立时复用proposal
epoch：

- previous identity正是最近成功retire的generation；
- 没有active reader；
- request fingerprint、padded count、lane和FullSource identity不变；
- `step == previous.step + 1`；
- previous phase为PROPOSAL或STEP。

任何abort会清空continuation资格；stale/ABA predecessor不能重新获得workspace。

### 13.2 Serialized lifecycle

```text
proposal begin / epoch acquire
  → step 0 materialize → validate → publish → forward → retire
  → snapshot E1
  → step 1 rematerialize → validate → publish → forward → retire
  → step 2 rematerialize → validate → publish → forward → retire
  → verify consumed steps == K
  → proposal epoch finish
```

当前retire发生在同一个serialized eager Python调用中、model forward返回之后。CPU状态机证明
active backing不会覆盖和stale handle会失败，但不证明真实NPU stream/event completion；这仍是
`G-AR-STEP` NPU Gate。

## 14. Ascend-only integration seam

vLLM没有修改。P4b复用P4a已经review过的最小Ascend vendor-local seam：

```text
DraftMetadataInputs
  → _validated_eagle3_read_inputs()          # the single validation boundary
  → AscendDraftAttentionReadInputs
  → _build_eagle3_private_attn_metadata()
  → upstream_speculator_module.build_attn_metadata(**explicit kwargs)
```

existing `build_attn_metadata_wrapper()`仍负责把原版vLLM module function指向Ascend builder；
existing `build_draft_attn_metadata_factory()`仍注入positions/is_prefilling。Window state不存入
wrapper、module global、ContextVar、closure或shared owner。

vendor-local duplication仅包括query-layout和builder kwargs assembly。未复制proposal、prepare
kernel、slot计算、forward、sampling或整个AR speculator。AST/signature drift guard是
`R-REPO-01`带来的显式维护成本。

## 15. Profile / Dummy / Prefill phase

### 15.1 Profile / dummy

eligible profile、dummy或`input_batch.is_dummy`：

- 不创建production epoch；
- 不freeze proposal；
- 不materialize workspace；
- 不publish Draft Window metadata；
- 执行真实baseline `_prefill()`。

### 15.2 Scheduler prefill vs Eagle3 first pass

`_prefill()`这个方法名不等于scheduler正在prefill。它是每个Eagle3 proposal的第一个Draft
forward。Review复核证明，upstream会在长prompt的每一个scheduler prefill chunk后调用
speculator；因此只要所有active row都仍是prefill，当前proposal就显式走baseline full-read
bypass，无论该chunk是continuing还是terminal。它不创建epoch/workspace/store，也不声称
Window化prefill。

```text
scheduler pure-prefill (continuing or terminal)
  → baseline full proposal；zero P4b state

decode proposal's Eagle3 _prefill first pass
  → real Window step 0；不能因方法名绕过

mixed prefill/decode
  → fail closed before epoch/workspace
```

专门测试证明continuing与terminal pure-prefill均不创建Window state，再用同一eligible harness
证明decode first pass创建真实proposal context。`G-PREFILL`仍OPEN：没有任何prefill proposal
使用Window read inputs。

## 16. Fail-closed Matrix

| Combination | Result before Window materialize |
|---|---|
| Eagle3 + static K + single dense GQA + serialized eager + TP1 | P4b candidate route |
| Window OFF | exact baseline |
| plain Eagle | P1 unsupported / no P2-P4 state |
| MTP / special MTP | P1 forced OFF / no state |
| dynamic speculative decoding | factory/P2 source gate raises before runtime workspace |
| DFlash / eligible DSpark | unchanged P4a route |
| DFlash2 | runtime unsupported；no P4b |
| graph FULL / FULL_DECODE_ONLY / PIECEWISE | P2 or live eager guard rejects |
| async | P2 runtime gate rejects |
| multi-group / non-dense GQA | P2 capability gate rejects |
| MLA / DSA / SFA / V4.1 / native / recycling | P2 capability gate rejects |
| TP>1 / DP>1 / PP>1 / PCP/DCP/SP / DSA-CP / FlashComm | P2 runtime gate rejects |
| prefix cache ON | P2 gate rejects |
| mixed prefill/decode | shared phase classifier rejects before epoch |
| pure scheduler-prefill（continuing或terminal） | explicit baseline-full bypass；zero Window state |

pure scheduler-prefill bypass是明确的phase contract，不是把一个已创建的eligible Window
generation静默降级；`G-PREFILL`不因此关闭。其它unsupported combination显式拒绝或按Frozen
forced-OFF policy保持baseline。

## 17. Tests

### 17.1 P4b test map

| Test area | What it proves | Failure meaning |
|---|---|---|
| short/exact/non-boundary | Frozen `S`数学独立于step | anchor math drift |
| K>=3 frozen anchor | `S0==S1==S2`且`E_s`变化 | per-step错误重算S |
| rejection | current proposal不重算；next proposal重算 | L0/rejection phase错误 |
| future block | `L0=64,K=3`能读下一physical column | step0 narrow view污染step1 |
| poisoned workspace | 每step从FullSource刷新 | window-of-window / stale clone |
| step continuation | same epoch、new generation、strict step | P3 lifetime contract破坏 |
| stale predecessor / ABA | 旧generation不能重新继续 | workspace可被stale handle占用 |
| same-pointer reorder | req order和in-place mapping rewrite被拒绝 | proposal freshness失效 |
| profile/dummy | baseline执行且zero P4b state | startup/profile regression |
| pure continuing prefill | baseline执行且zero epoch/workspace/store | long prompt在进入decode前被运行期中止 |
| first-pass L0 | CPU mirror冻结且无feature D2H | L0 provenance错误 |
| one decode snapshot | E1 D2H只一次，later step host derive | sync策略或step math漂移 |
| first-pass private metadata | query/positions/full slot/Target invariants | read/write边界破坏 |
| Tensor/NumPy isolation | nested Target storage不alias | Target污染 |
| decode build/forward/retire | exact FIA carrier、store owner和每步lifecycle | stale metadata/backing或upper冒充exact |
| builder returns Target alias | state写入前隔离 | Target attn_state污染 |
| missing/empty Target | builder前hard fail | isolation绕过 |
| graph live guard | graph在materialize前拒绝 | unsupported route误enable |
| builder/forward exception | store和lease清理 | generation泄漏 |
| upstream drift guard | launchers与三个真实kernel的K/L0/step contract | silent upstream drift |

### 17.2 Final local results

测试环境使用原版vLLM source checkout；因editable source没有release version metadata，host UT
设置`VLLM_VERSION=0.29.0`只用于选择当前main兼容分支，不是production dependency。

| Scope | Result | Limitation |
|---|---|---|
| review focused CB-01/FB-01/FB-02 | `4 passed` | CPU/static only |
| P4b targeted `test_draft_window_eagle3.py` | `31 passed` | CPU/static only |
| P4a targeted `test_draft_window_eager.py` | `40 passed` | shared phase classifier regression |
| P1-P4b + DFlash2/DSpark + BlockTables + attn_utils/attention | `367 passed, 23 subtests passed` | no NPU |
| `attention/test_attention_v1.py` | `41 passed, 2 subtests passed` | exact-vs-upper CPU metadata test |
| locally runnable `tests/ut/spec_decode`（VWN file excluded） | `470 passed, 13 skipped, 2 subtests passed` | no NPU |
| full `tests/ut/spec_decode` | `472 passed, 13 skipped, 7 failed, 2 subtests passed` | 7 VWN host backend failures；不是PASS |
| P4a parent VWN comparison | same `7 failed, 2 passed` | failures occur during model construction before P4b path |
| Ruff check / format | PASS | five review-fix files |
| targeted Mypy | PASS | `draft_window_eager.py` + `draft_window_eagle3.py`；source PYTHONPATH |
| compileall / `git diff --check` | PASS | changed scope |
| selected repository hooks | PASS | ruff、codespell、typos、filename、package-init、logger、imports、boolean-with、long-function、symbolic-meta |
| full pre-commit aggregate | environment-blocked | actionlint Go archive truncated；gitleaks binary absent且host无`wget`；不是PASS |

7个full-suite failures全部来自`test_speculators_vwn_eagle3.py`构造Vwn Llama attention时的
`ValueError: Invalid attention backend for None`。P4a parent在同一Python/vLLM/env下得到同一
7项失败，因此不能记作P4b PASS，但可归因于既有host platform/mock环境。

## 18. NPU Test Plan

固定环境：single card、TP1、DP/PP/PCP/DCP/SP=1、dense GQA、normalized Eagle3、static
K（至少3）、eager、async false、prefix cache off、fixed seed；vLLM exact baseline加C5 Ascend。

每个case执行A/B：

```text
A: draft_window_size OFF
B: draft_window_size ON
```

| Case | Geometry / event | Required evidence |
|---|---|---|
| N01 | short context `H<=W` | `S=0`，A/B read visibility等价，write/Target相同 |
| N02 | exact anchor boundary | CPU plan与physical read-set一致 |
| N03 | non-boundary long context | aligned S与Window exact/upper一致 |
| N04 | `B=16,W=64,K=3,L0=64` | step 0→1 future physical column出现且无stale table |
| N05 | first pass→step1→step2 | `S`冻结，`E_s/V_s`逐步记录 |
| N06 | rejection in same block | E1扣rejection，S不变 |
| N07 | rejection crossing block boundary | columns/visible length与oracle一致，next proposal新S |
| N08 | long context | stable bounded workspace与correct read-set |
| N09 | request reorder | new epoch/fingerprint；无串请求 |
| N10 | finish/add or same-row replacement | stale generation不能复用 |
| N11 | profile/dummy startup | baseline path、zero production Window state |
| N12 | unsupported samples | dynamic K/graph/async/prefix/TP2等显式fail closed |

N03/N08若由scheduler切成多个pure-prefill chunk，预期不是每个prefill chunk都Window化：A/B在
这些chunk均走baseline full read并保持zero Window state；prompt完成后，第一个pure decode
proposal才建立`L0/H/S`并进入P4b Window。mixed prefill/decode batch仍应在epoch前拒绝。NPU
采样报告必须把这段phase transition单独列出，不能把prefill full read误判为Window失效。

每case必须记录：

- vLLM/Ascend commit、model/config/seed/command；
- proposal `L0/K/H/S`；
- 每step `E_s/V_s`；
- P2 descriptors、valid counts、FullSource columns；
- materialized Window table/lengths；
- absolute positions、query layout、physical slot mappings；
- actual Draft Attention physical operand/read-set；
- Draft tokens/logits（可获取时）；
- Target metadata identity/content/lengths/logits；
- final output；
- stream/event completion与workspace reuse timing；
- D2H/H2D/kernel profiler。

关闭`G-AR-STEP`的最低条件：B的真实physical read-set等于CPU oracle；A保持baseline；
write/query/Target invariants A==B；first-pass和所有AR step均正确；没有reader完成前覆盖；性能
profiling无未批准同步/回归。

## 19. Runtime Effect

P3结束时Attention仍读取baseline full context。P4a只接通parallel DFlash/DSpark。

P4b代码现在把eligible Eagle3 first-pass和每个AR step的Draft metadata read table/lengths接到
Ascend builder，因此这是Eagle3 Window read visibility的第一次真实production wiring。

但本地证据只证明：

- typed inputs到metadata builder的静态数据流；
- CPU state machine与owner/invariant；
- unsupported route fail closed。

本地证据不能证明NPU attention kernel实际访问的physical block集合、stream完成时刻或性能。
所以准确状态是“implemented static candidate”，不是runtime support。

## 20. P4a Regression

P4b初始C5没有修改P4a专有文件；review-fix为关闭CB-01，修改了P4a/P4b共享的
`draft_window_eager.py` pure-prefill classifier。DFlash/DSpark class/MRO、Ascend CPU-exact seam、
eligible decode Window path与read/write invariant均未改变。P4a现在与P4b一致：任何pure
scheduler-prefill chunk显式走baseline且zero Window state；mixed prefill/decode仍在materialize
前拒绝。

共享P3 runtime只增加了Eagle3-only `materialize_serialized_step()`；普通P4a
`materialize()`仍要求mapping epoch严格增加。P4a、DFlash、DSpark和DFlash2相关回归均包含在
367项绿色套件中。

`G-GQA-EAGER`仍为OPEN，不因P4b CPU tests改变。

## 21. Remaining Gates

| Gate | Status |
|---|---|
| P4b independent review + Codex adjudication | **CLOSED — STATIC PASS** |
| `G-AR-STEP` | OPEN — company NPU required |
| P4a `G-GQA-EAGER` | OPEN — company NPU required |
| real NPU lifecycle/completion | OPEN |
| P4b D2H/performance | OPEN — one feature E1 D2H/proposal must be profiled |
| Graph capture/replay | BLOCKED |
| Async multi-lane | BLOCKED |
| prefix cache / mixed/function/Window化chunked prefill | BLOCKED；pure scheduler-prefill仅baseline bypass |
| TP/DP/PP/PCP/DCP/SP/DSA-CP/FlashComm | BLOCKED |
| MLA/DSA/SFA/V4.1/native/recycling/multi-group/DFlash2 | BLOCKED |
| delivery manifest / feature release | HOLD |

## 22. Developer Reading Guide

建议顺序：

1. upstream `vllm/v1/worker/gpu/spec_decode/speculator.py:88-96`：configured K来源。
2. upstream `autoregressive/speculator.py:204-370`：proposal、first pass、rejection-corrected decode入口。
3. upstream同文件`:440-645`：first pass、per-step metadata/slot/forward顺序。
4. upstream同文件`:758-981`：prefill/decode/update kernels的L0/E语义。
5. `draft_window_eagle3.py:40-69`：immutable proposal/step types。
6. 同文件`:101-194`：static-K init、proposal epoch、profile/prefill classification。
7. 同文件`:197-370`：first pass L0、E1 snapshot、per-step materialize。
8. 同文件`:373-433`：single validate boundary和retirement。
9. 同文件`:449-545`：Frozen S与per-step math。
10. `draft_window.py:463-540`：P2 frozen-step projection。
11. 同文件`:2012-2189`：P3 serialized continuation与lease owner。
12. `autoregressive/speculator.py:276-349`：Ascend outer proposal scope。
13. 同文件`:448-659`：first-pass和AR live consumption/retirement。
14. 同文件`:664-766`：vendor-local Draft-private metadata与Target isolation。
15. `tests/ut/spec_decode/test_draft_window_eagle3.py`：先读math/future block，再读lifecycle和integration tests。

## 23. Mental Model

1. 一个Eagle3 proposal只有一个mapping epoch，但每个step有独立generation。
2. `L0`在rejection前冻结；`E1`在rejection后读取。
3. `S`只由`L0+K`算一次；`E_s`每step变化。
4. 每step从FullSource刷新，永不从上一Window再切。
5. first pass也必须使用Draft-private metadata，不能Window化Target object。
6. Window只改变Draft read table/length；slot、positions、query和Target保持full。
7. 前一reader成功retire后，下一step才可复用固定workspace。
8. profile/dummy与所有pure scheduler-prefill chunk走baseline；Eagle3 decode first pass不绕过。
9. vLLM精确不变；Ascend local assembly由drift/parity tests保护。
10. CPU/static implementation不等于NPU runtime Gate关闭。

## 24. P4b Independent Review Resolution

### 24.1 Review metadata

| Item | Value |
|---|---|
| reviewer | DeepSeek Independent Review（用户提供文本） |
| review target | C5 `d0c8883816f0e1fe333dc9f3197d3c4e47c475a5` |
| adjudication baseline | vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c` clean；P4a Final `4c1f69146915f4f0ae5a6a61371ebfe181237d8f` |
| review-fix | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` |
| adjudication time | 2026-10-11 14:06:33 +0800（Asia/Shanghai） |

Finding统计：`ACCEPTED=4`、`PARTIALLY_ACCEPTED=2`、`REJECTED=0`、
`OPTIONAL_STYLE_ONLY=1`、`ARCHITECTURE_ESCALATION=0`。真实NPU read-set、stream ordering、
logits与性能不属于静态Finding关闭范围，统一保持`NEEDS_NPU_VERIFICATION`。

### 24.2 Resolution table

| ID | Severity | Finding | Resolution | Evidence | Code/Test/Doc Change |
|---|---|---|---|---|---|
| CB-01 | Critical | continuing pure chunked-prefill在runtime抛错，长prompt默认路径无法到decode | **ACCEPTED** | upstream每个target step后均调用speculator；原classifier在epoch前抛`NotImplementedError`；两个新增测试在C5上均red | shared classifier把所有pure scheduler-prefill明确归为baseline-full bypass；mixed仍拒绝；P4a/P4b测试验证zero epoch/workspace/store |
| FB-01 | Major | Window分支跳过post-forward Ascend length mutation，FIA carrier parity未证 | **PARTIALLY_ACCEPTED** | 接受缺少直接carrier test；拒绝改用upper：upstream eager loop每step在forward前重建metadata，post-forward mutation不会进入下一forward；Final §9.6要求exact；Attention builder test证明`69 exact != 74 upper`时FIA字段取69 | 无production语义修改；新增exact-vs-upper backend test及full-exact减proposal-frozen `S` differential；本文补清调用链 |
| FB-02 | Major | drift guard只钉launcher，未钉真正定义`E_s`的三个kernel | **ACCEPTED** | 原expected字典只有`prepare_*`/`update_*` launcher；kernel body含rejection correction和逐step `+1` | guard新增三个kernel AST hash |
| FB-03 | Minor | `W>=K`仍可能在rejection后runtime abort，应更强gate或`V=0` | **PARTIALLY_ACCEPTED** | 接受场景可达且必须显式记录；拒绝视为实现bug或采用建议修复：Final I24、§9.3与T04要求逐step fail closed，`W>=K`只证明初始几何；`V=0`违反`S<=E_s`，全局更强gate会误拒安全residue | 保留现有production与rejection regression；补充配置/运行期边界说明 |
| FB-04 | Minor | Notes把`V_s`错误写成clamp到`W` | **ACCEPTED** | production先断言`S<=E_s<=H`，随后`V_s=E_s-S`；容量上界是`W+B-1` | 修正文档公式与capacity解释 |
| FB-05 | Minor | pure-prefill baseline bypass与MRV1/read-set预期差异未记录 | **ACCEPTED** | phase classifier与zero-state tests可复现；NPU A/B在prefill阶段应看到baseline full read | 记录continuing/terminal pure-prefill都baseline，Window从decode proposal开始；NPU计划补phase预期 |
| FB-06 | Style | 跨模块import私有isolation helper | **OPTIONAL_STYLE_ONLY** | helper是vendor-internal、无外部API承诺；当前引用单一且测试完整，移动/公开不会改变正确性 | 本轮不扩大public surface；无代码变更 |

### 24.3 Red-to-green evidence

- CB-01：review前两个pure-continuing测试均以同一`NotImplementedError`失败；review-fix后均通过。
- FB-02：guard加入placeholder后对三个kernel hash显式失败；填入当前exact baseline AST hash后通过。
- FB-01是“证据缺口”而非接受的production bug；没有伪造review前red。新增tests锁定exact carrier、
  planning upper不进入FIA exact字段，以及每step full exact与Window exact之差恰为frozen `S`。

### 24.4 Final diff summary

| File | Final review change |
|---|---|
| `draft_window_eager.py` | pure scheduler-prefill（continuing/terminal）统一显式baseline bypass；mixed仍fail closed |
| `draft_window_eagle3.py` | 跟随shared classifier重命名；Eagle3 decode first-pass逻辑不变 |
| `test_draft_window_eager.py` | continuing pure-prefill red/green与zero P3/P4 state |
| `test_draft_window_eagle3.py` | Eagle3 continuing bypass、FIA exact differential、三个kernel drift hashes |
| `test_attention_v1.py` | AR explicit exact与planning upper分离的backend carrier test |

### 24.5 Final tests

| Command / scope | Result | Limitation |
|---|---|---|
| focused CB-01/FB-01/FB-02 regressions | `4 passed` | CPU/static |
| `pytest -q tests/ut/spec_decode/test_draft_window_eagle3.py` | `31 passed` | no NPU |
| `pytest -q tests/ut/spec_decode/test_draft_window_eager.py` | `40 passed` | no NPU |
| combined P1-P4b/backend/BlockTables/attn | `367 passed, 23 subtests passed` | no NPU |
| locally runnable `tests/ut/spec_decode` | `470 passed, 13 skipped, 2 subtests passed` | excluded known-host VWN file |
| full `tests/ut/spec_decode` | `472 passed, 13 skipped, 7 failed, 2 subtests passed` | same seven `Invalid attention backend for None` host failures as P4a/C5；不是PASS |
| Ruff check / format | PASS | five review-fix files |
| Mypy `--follow-imports=skip` | PASS | two changed production modules；source PYTHONPATH required |
| compileall / `git diff --check` | PASS | review-fix scope / final lineage |
| executable repository hooks | PASS | ruff、codespell、typos、filename、init、logger、imports、boolean-context、long-function、symbolic-meta、suggestion |

### 24.6 Final invariant audit

- `L0`仍是proposal-entry full exact、pre-rejection；`K`仍是configured static K；dynamic K拒绝。
- `H=L0+K`；`S`proposal-frozen；`E_s`来自rejection-corrected step state；每step`S<=E_s<=H`。
- first-pass与每个AR step均从canonical FullSource materialize；future column与poisoned-window tests通过。
- slot mapping、positions、query layout、Target owner/content与full table均不被Window修改。
- stale step、active reader、ABA、reorder与same-row replacement仍被拒绝。
- pure scheduler-prefill不创建epoch/workspace/store；mixed仍拒绝；decode first-pass不被prefill bypass。
- 无module-global、ContextVar、shared-owner swap、vLLM修改或prototype dependency。
- P4a DFlash/DSpark targeted tests继续通过。

### 24.7 Exact static route and unsupported routes

静态候选仅为：normalized Eagle3、configured static `K>0`、single executable dense-GQA group、
serialized eager、graph NONE、async false、TP/DP/PP/PCP/DCP/SP均为1、DSA-CP/FlashComm false、
prefix cache off；pure scheduler-prefill阶段仅baseline bypass，Window从pure decode proposal开始。

plain Eagle、MTP、dynamic K、DFlash2、Graph、Async、multi-group、MLA/DSA/SFA/V4.1/native/
recycling、parallel topology、prefix cache与mixed prefill/decode均不受支持并保持各自fail-closed或
Frozen forced-OFF contract。

### 24.8 NPU evidence and final gate

没有公司NPU runtime report。以下仍为`NEEDS_NPU_VERIFICATION`：实际Eagle3 Attention physical
read-set、真实stream ordering、Draft proposal/logits、Target logits equality、每proposal D2H与
latency影响、serialized multi-step completion timing。M-02性能Gate保持OPEN。

最终状态：

`P4b STATIC FINAL: PASS`

`G-AR-STEP: STATIC CONTRACT PASS / NPU RUNTIME OPEN`

`P4a G-GQA-EAGER: OPEN — NPU REQUIRED`

`Feature release: HOLD`
