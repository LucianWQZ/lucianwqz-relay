# P7-X Graph Eagle3 Architecture

## Executive Decision

Eagle3 can reuse the common P6 provider, capture/runtime identity framework, stable backing rules, and source-spy schema. It cannot reuse the DFlash capture helper because its autoregressive Graph manager captures a first pass and multiple ordered Draft steps with different metadata consumers.

```text
GRAPH_EAGLE3_ARCHITECTURE: READY WITH DISTINCT CAPTURE ADAPTER
IMPLEMENTED: NO
NPU VERIFIED: NO
PUBLIC GRAPH GATE: FAIL-CLOSED
```

## Current Source Owners

- `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py::AutoRegressiveAclGraphManager`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py::AutoRegressiveAclGraphManager.capture`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py::AutoRegressiveAclGraphManager.run_fullgraph`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py::AscendAutoRegressiveSpeculator`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py::_build_draft_attn_metadata`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py::build_draft_attn_metadatas`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py::_multi_step_decode`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eagle3.py` for P4b proposal math and lifecycle

The pinned vLLM generic autoregressive capture creates its own baseline/dummy structures. Ascend owns the runtime AR metadata assembly and Graph manager path, but a product-safe capture adapter has not been implemented.

## Why DFlash Is Not the Adapter

DFlash/DSpark submit a parallel Draft query with one method-specific query width. Eagle3 has:

- first-pass Draft metadata that baseline may derive from Target state;
- configured static K;
- proposal-frozen anchor S;
- a list/sequence of per-step metadata consumers;
- per-step exact end `E_s` and visible length `V_s`;
- rejection and future-column behavior;
- one proposal identity spanning several ordered consumers.

Forcing Eagle3 through `dflash/capture.py` would lose step ordinals and first-pass isolation.

## Proposed Capture Identity

Use one proposal capture identity plus consumer identities:

```text
Eagle3CaptureIdentity
  method=eagle3
  route=first_pass_and_ar_steps
  graph_mode
  global_gid
  backend/builder identity
  static_k
  query/layout schema
  padded batch/token geometry
  descriptor/bucket
  execution lane
  provider schema/version
  backing-bank geometry

Eagle3ConsumerIdentity
  capture identity
  phase=FIRST_PASS | AR_STEP
  step ordinal
  consumer ordinal
  backing identity
```

No request id, generation id, or mapping epoch is fabricated at startup. Runtime generation compatibility is checked separately.

## Persistent Carrier Bank

Minimum bank:

- one first-pass table/exact/upper and Draft-private metadata backing;
- one entry per captured AR step (or a source-proven indirect operand layout);
- generation/step tags for table, exact, upper, and derived metadata;
- stable address, fixed capacity, mutable content;
- completion accounting for all consumers.

The safest initial design is descriptor × consumer ordinal. Sharing one backing across steps is disallowed unless NPU trace proves each step completes before the next overwrite and capture reads the same indirection safely.

## Runtime Math and Flow

At proposal entry:

```text
L0 = full exact before proposal rejection correction
K  = configured static speculative width
H  = L0 + K
S  = B * floor(max(H - W, 0) / B)
```

S is frozen for the proposal. For each actual consumer:

```text
E_s = current source-derived exact end for that real step
validate S <= E_s <= H
V_s = E_s - S under the established aligned-capacity contract
```

Runtime flow:

```text
proposal begin
-> acquire generation and validate static K
-> bind canonical FullSource
-> materialize first-pass Window
-> build Draft-private first-pass metadata
-> refresh first-pass carrier
-> for each captured AR step:
     update full positions/seq/slot state
     derive real E_s
     materialize again from canonical FullSource
     refresh matching step carrier
-> validate all consumer generations/ordinals
-> replay
-> observe consumers/update
-> wait for real completion
-> retire proposal bank
```

The previous step's Window table is never a source.

## First-pass Isolation

Window OFF keeps baseline reuse behavior. Window ON must create Draft-private Graph metadata. Before and after build, assert Target owner identity and nested tensor/NumPy storage are unchanged. Query layout, positions, and full slot mapping preserve baseline values. Only Draft read table/length/derived read fields differ.

## Rejection and Future Column

Rejection may change per-step exact ends but does not recompute S during the proposal. A future block column must be fetched from canonical FullSource for the later step. The canonical test case remains:

```text
B=16, W=64, K=3, L0=64, H=67
```

Step 0 cannot cap the columns available to steps 1/2. Rejection crossing the anchor either satisfies the established static P4b contract or fails closed before replay; Graph may not invent a different rule.

## Capture Adapter Seams

Expected code locations:

- a new Ascend-owned Eagle3 capture adapter adjacent to `autoregressive/aclgraph.py`;
- provider installation on the AR speculator/manager instance;
- consumer identity registration from the actual captured metadata list;
- runtime binding in `run_fullgraph` before the metadata consumer;
- P6 attribution/update hooks retained, not replaced;
- common carrier and spy types reused from `draft_window_graph.py` and the characterization module.

No vLLM patch, global transport, `ContextVar`, Target swap, or copied AR speculator is permitted.

## Fail-closed Matrix

- plain Eagle;
- dynamic K;
- missing/duplicate step consumer;
- S drift within one proposal;
- table/length generation mismatch;
- first-pass Target-derived fallback while provider exists;
- previous Window used as source;
- rejection leaves `E_s` outside the frozen interval;
- graph descriptor/static-K/query geometry mismatch;
- unsupported multi-group/backend/topology/async/prefix/mixed route;
- unresolved completion/lifetime.

## Red Test List

1. capture identity and runtime generation types cannot be mixed;
2. provider exists but first pass uses Target-derived metadata -> hard fail;
3. K=3 registers first pass plus every real AR consumer;
4. S0=S1=S2 while E/V change;
5. step table and length always share generation/ordinal;
6. stale or duplicate step rejected;
7. corrupt previous Window then confirm next step uses FullSource;
8. future block appears at later step;
9. rejection does not move S;
10. Target tensor and NumPy storage remain isolated;
11. full slot/positions/query parity;
12. A/B/A' stable addresses with different generations;
13. exception cleanup releases every bound consumer;
14. plain Eagle/dynamic K/profile/dummy routes do not install live state.

## NPU Campaign

Use static K >= 3 and collect actual operand addresses/read sets for first pass and every AR step. Cases: short, aligned boundary, non-boundary, future column, rejection same/cross block, long context, A/B/A', and request reorder if available. Record slot/write, Target metadata/logits, Draft proposals/logits, stream/event completion, and profiler trace.

Eagle3 can be implemented after base G1–G5 without waiting for DSA/SFA, but it requires its own local implementation and NPU branch. A DFlash Graph pass is not evidence for Eagle3.

