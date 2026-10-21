# P6A Codex Final Review Adjudication and Graph-Track Freeze

## 1. Document Status

| Item | Final value |
|---|---|
| Phase | P6A review adjudication；不是P7 |
| Adjudication date | 2026-10-14（Asia/Shanghai） |
| Independent Review | `P6A_DeepSeek_Independent_Review.md` |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |
| vLLM state | clean，zero diff，未修改 |
| vLLM-Ascend P6 Final | `7599497ab2694c4cf343f61f82f449980d8bad93` |
| P6 Final tree | `b4f7d12bd24b0a7632f9e606b29703a7c96278de` |
| vLLM-Ascend state | clean，未修改production/test |
| P6A production/review-fix commit | 无；Not-found路径不制造空commit |
| Final outcome | `NOT_FOUND_AFTER_REVIEW` |

本报告以当前checkout源码与可复现测试为第一证据。Final Design、Implementation Plan、P6
Final Notes、P6A Search Ledger与DeepSeek Review均已完整读取；文档旧行号不覆盖当前源码事实。

## 2. Executive Decision

DeepSeek的核心纠正成立：P6A原报告把所有route概括成“Ascend只能在upstream dummy metadata
构建前传递传统owner”，这对Eagle3 AR decode不成立。AR decode真正送入FIA consumer的
per-step metadata由Ascend `_build_draft_attn_metadata`构建。

但该纠正没有产生一个合法A类seam：

- Eagle3 AR/first-pass现有Window分支依赖live proposal、mapping epoch与P3 generation；startup
  capture没有这些runtime身份，并受Graph mode硬闸阻止；
- DFlash/DSpark capture metadata仍由pinned vLLM helper构建，没有Ascend method-level carrier；
- backend `full_graph_fia*`虽然是operator前最后Ascend点，但没有现成P6 provider、CaptureIdentity、
  descriptor/bucket、consumer ordinal或write-side reference通路；
- 建立capture-scoped transport/state、Draft-private capture assembly或backend carrier是新设计，
  属于owner本轮未授权的B侧工作，不是“已经存在但遗漏”的A；
- 修改vLLM属于C，R-REPO-01及owner决策均禁止。

因此P6A Outcome B保留，但freeze理由由“技术不可能/metadata完全不可达”修正为：

> pinned baseline中没有已经存在、满足全部安全判据的Ascend-owned pre-capture injection seam；
> 继续接通必须进入当前未授权的B或C。

## 3. Resolution Table

| ID | Severity | Finding | Reproduction | Resolution | Evidence | Action |
|---|---|---|---|---|---|---|
| F-01 | Major | 原报告称Ascend manager只能在upstream dummy metadata前传传统owner；Eagle3 AR真实metadata由Ascend构建 | 复现成立 | `ACCEPTED` | Ascend `AutoRegressiveAclGraphManager.capture`丢弃generic prepare返回；upstream AR loop调用`self._build_draft_attn_metadata`并动态派发至Ascend override；capture外层`build_attn_metadata_wrapper`切换到Ascend builder | 重写Ledger、P6A Notes与Plan的route-specific调用链；撤销过强论据，不改变Not-found结果 |
| F-02 | Minor | 原论证只写generic prepare返回被丢弃，漏写真正per-step consumer | 复现成立 | `ACCEPTED` | 真正consumer metadata来自Ascend override；其Window分支需要live proposal/P3 generation，capture期不存在 | 补齐consumer来源及capture-scoped read-source缺口 |
| F-03 | Minor | P6 Final production docstring对Eagle3 AR metadata ownership表述过宽 | 复现成立 | `ACCEPTED` | `observe_draft_window_graph_capture`中“upstream builds private dummy metadata”适用于DFlash/initial dummy，不适用于AR per-step metadata | 保持P6 Final production SHA不变；在canonical P6A docs作明确勘误，未来owner授权production维护时再收紧注释 |
| F-04 | Minor | P7 Eager前置必须说明Graph配置是hard fail，不是自动fallback | 复现成立 | `ACCEPTED` | `draft_window.py::_runtime_capability_failures`把`graph_mode != NONE`记为failure，Gate随后抛`NotImplementedError`；Eagle3另有三处runtime Graph硬闸 | Plan固定P7 Eager只接受`graph_mode=NONE`或等价`enforce_eager`，禁止依赖fallback |
| Q-01 | Question | Freeze应写成新capture-scoped transport“未授权”而非“不可实现”，并询问该形态是否属于B | 技术区分成立；再次询问owner在本轮无必要 | `PARTIALLY_ACCEPTED` | 当前owner指令只授权查找已经存在的A；A失败后明确不批准B/C。任何新增capture-scoped transport均超出本轮授权，不论未来如何命名 | 用authorization boundary支撑freeze；不替owner设计或选择B/C |
| Q-02 | Question | host/static不能证明captured实际地址、effective generation或NPU timeline | 复现成立 | `ACCEPTED` | P6 timeline保留unknown effective generation/`NEEDS_NPU_TIMELINE`；本轮没有NPU trace | 保持`P6 NPU GRAPH: NOT VERIFIED`，未来Graph重启后独立验证 |

统计：`ACCEPTED=5`，`PARTIALLY_ACCEPTED=1`，`REJECTED=0`，
`INSUFFICIENT_EVIDENCE=0`。

没有被Review证明为假阳性的`VALID_SEAM`需要撤销，因为P6A从未宣称找到seam；被撤销的是原
Not-found报告中的过强首要理由。

## 4. Independent Source Reproduction

### 4.1 Eagle3 first-pass capture

```text
AscendAutoRegressiveSpeculator.capture
  → prefill_cudagraph_manager.capture(self._prefill, Target model_state, ...)
  → Ascend AutoRegressiveAclGraphManager.capture
  → upstream SpeculatorCudaGraphManager.capture
  → upstream prepare_inputs_to_capture builds initial dummy state
  → Ascend _prefill executes before Draft forward
  → full_graph_fia* consumes the resulting attn_metadata
```

Ascend `_prefill`结构上能以Draft-private metadata替换传入metadata，但当前Window分支只在
`_eagle3_window_is_active()`时进入；该条件依赖live P3 proposal generation。它又明确拒绝
`cudagraph_runtime_mode != NONE`。因此这是潜在新B设计位置，不是现有A seam。

### 4.2 Eagle3 AR decode capture

```text
Ascend manager local create_forward_fn
  → prepare_inputs_to_capture(...) return value discarded
  → Ascend _multi_step_decode
  → upstream per-step loop
  → self._build_draft_attn_metadata(...)
  → dynamic dispatch to Ascend override
  → Ascend builder metadata
  → full_graph_fia* actual consumer
```

这条链直接接受F-01。Ascend不是被排除在metadata之外；现有缺口是capture期没有合法P6 Window
source。当前Window branch调用`_materialize_eagle3_decode_step`，要求live proposal、generation、
mapping epoch与Target metadata；这些不能用fake generation 0/request/epoch替代。

### 4.3 DFlash / DSpark capture

```text
DFlashAclGraphManager.capture
  → upstream DFlashCudaGraphManager.capture
  → upstream _prepare_dflash_inputs_to_capture
  → dummy table / slot / length / metadata
  → _generate_draft
  → Ascend full_graph_fia*
```

`AscendDFlashSpeculator`没有capture、`_generate_draft`或`_build_draft_attn_metadata`的等价
pre-capture override。DSpark继承这条capture机制。当前无method-level carrier seam。

### 4.4 Backend与compilation边界

`AscendAttentionBackendImpl.full_graph_fia/full_graph_fia_v2`从最终`attn_metadata`读取table与
length，并在graph task begin/end范围内捕获operator，是最后Ascend-controlled点。但现有签名/
实例没有P6 provider、CaptureIdentity、bucket、route、step ordinal或Target/write reference。
增加这些协议是新的backend transport，即未授权B。

`update_full_graph_params -> backend.update_graph_params`发生在replay/update侧。P6已静态接通，
但它不是startup pre-capture injection seam，也不能由host source证明UPDATE(N)的实际生效代际。

## 5. Why No Existing A Seam Exists

A类seam必须同时满足：实际operand确定前、能改变Draft read table/length、instance-owned、无
global/ContextVar/monkeypatch/owner swap、不污染Target/write、OFF exact no-op、不改vLLM、不复制
upstream capture manager，并且已经存在。

逐层搜索后的最近候选均至少缺一项：

| Candidate | Missing condition | Final classification |
|---|---|---|
| Eagle3 `_prefill` / `_build_draft_attn_metadata` | 无capture-scoped合法read source；Graph硬闸关闭 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| DFlash/DSpark manager参数 | upstream helper无provider/descriptor sink | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| `build_attn_metadata_wrapper` | module-global function replacement、非instance-owned | `SHARED_MUTATION` |
| `full_graph_fia*` | 无现成P6 attachment/identity/ordinal协议 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| `GraphParams` / task registry | module-global capture结果存储，不选择read source | `SHARED_MUTATION` / `NOT_RELEVANT` |
| `update_full_graph_params` | replay/update阶段，非pre-capture | `REPLAY_ONLY` |
| 修改pinned vLLM helper | 违反R-REPO-01 | `REQUIRES_VLLM_CHANGE` |

DeepSeek独立覆盖相同六类搜索面，未发现第七个明显入口；允许`SEARCH EXHAUSTED`。

## 6. Fail-Closed and Runtime-Inert Evidence

1. `draft_window.py::_runtime_capability_failures`对`graph_mode != "NONE"`产生capability failure；
   Window route在配置/admission阶段不是自动fallback。
2. Eagle3 Window路径在`_generate_draft`、`_multi_step_decode`、`_prefill`分别拒绝Graph mode。
3. `observe_draft_window_graph_capture`在provider存在时无条件hard fail，不允许fake generation进入
   startup capture。
4. provider存在但explicit carrier缺失/不匹配时，P6 metadata consumer hard fail，不能让Target
   carrier获胜。
5. `install_draft_window_graph_binding_provider`在非测试production中没有调用者；当前P6 provider
   机制运行时惰性，不会意外开启Graph。
6. provider不存在时，P5/P6 hooks全部保持OFF-path no-op/baseline。

## 7. Verification

执行：

```bash
env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window_graph_binding.py \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py
```

结果：

```text
69 passed, 1 warning in 0.10s
```

warning是pinned checkout缺少生成的`vllm._version`，与P6A无关。P6A没有production/test改动，
因此没有review-fix commit，也没有为了形式重复全套P1–P6测试；P6 Final完整回归证据仍由P6
Final Notes与review resolution承担。

## 8. Repository Audit

```text
vLLM HEAD   = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM tree   = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
vLLM status = clean

vLLM-Ascend HEAD   = 7599497ab2694c4cf343f61f82f449980d8bad93
vLLM-Ascend tree   = b4f7d12bd24b0a7632f9e606b29703a7c96278de
vLLM-Ascend status = clean
```

本轮没有：branch、commit、production/test diff、vLLM private patch、capture workaround、Graph
Gate修改或P7代码。

## 9. Graph-Track Freeze

```text
GRAPH TRACK STATUS:
FROZEN AT P6

Reason:
No existing Ascend-owned pre-capture injection seam in pinned baseline.

Not authorized:
B vendor-local capture assembly
C vLLM modification

Resume triggers:
owner approval / repository-boundary change / new upstream seam /
new backend-owned seam evidence.
```

Graph仍是最终Required方向。Freeze表示当前工程轨道停止，不表示需求取消。所有Graph-dependent
routes继续继承`GRAPH_BLOCKED`；P6 replay/update static carrier不能被外推为capture/NPU支持。

Graph Track恢复后仍必须取得：captured actual address、descriptor/bucket binding、Graph A/B/A、
UPDATE effective generation、physical read-set、stream lifetime/no-early-overwrite、recapture与性能证据。

## 10. P7 Entry Boundary

P7仅可进入Eager Track，并必须：

- 明确要求`graph_mode=NONE`或产品配置中的等价`enforce_eager`；
- 不依赖Graph配置自动fallback；
- 不安装/启用Graph provider；
- 不修改Graph capture，不解除FULL/FULL_DECODE_ONLY/PIECEWISE fail-closed；
- 不把P6A Freeze当作删除Graph最终需求；
- 不把Eager工作结果扩大为Graph支持。

本报告不启动P7。

## 11. Final Verdict

```text
P6A ASCEND-OWNED CAPTURE SEAM: NOT FOUND AFTER REVIEW
P6 STATIC FINAL: PARTIAL
P6 CAPTURE PATH: FROZEN BLOCKED
P6 GRAPH READ CARRIER: PASS (replay/update host-static path only)
P6 CAPTURE IDENTITY: PASS
P6 NPU GRAPH: NOT VERIFIED
GRAPH USER GATE: STILL FAIL-CLOSED
GRAPH TRACK: FROZEN
B/C: NOT AUTHORIZED
P7 EAGER TRACK: READY BY OWNER DIRECTION
FEATURE RELEASE: HOLD
```
