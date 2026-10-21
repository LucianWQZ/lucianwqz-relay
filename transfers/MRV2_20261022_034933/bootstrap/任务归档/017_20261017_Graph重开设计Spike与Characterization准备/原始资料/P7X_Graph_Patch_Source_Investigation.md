# P7-X Graph Patch Source Investigation

## 1. Status

This document records the source investigation and architecture adjudication for
the local patch-based Draft Window startup-capture spike. It is not a Graph
support declaration.

| Item | Exact value |
|---|---|
| vLLM-Ascend source baseline | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |
| vLLM-Ascend baseline tree | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` |
| Local spike branch | `spike/p7x-draft-window-graph-patch` |
| Local spike commit | `c43989aabd9b40a561987d39f4ba4516934f2f5b` |
| Local spike tree | `5caecd1613206904a59960c23f22883115a9fd96` |
| Pinned vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| Pinned vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |
| NPU execution | Not run |
| Public Graph Window Gate | Still fail closed |
| Push status | Local commit only; not pushed |

## 2. Product fact separated from this spike

The current supported delivery shape can use Target graph while keeping the
Draft speculator eager. `AscendDFlashSpeculator.init_cudagraph_manager()` and
`AscendDSparkSpeculator.init_cudagraph_manager()` set only the Draft query graph
manager to `NONE` when `speculative_config.enforce_eager` is true. They do not
disable the Target model runner graph.

Historical Phase 1/2 evidence under `Note/MRV2/测试` used Target
`FULL_DECODE_ONLY`, Draft `enforce_eager=true`, MRV2, and Window ON.

```text
CAN_TARGET_GRAPH_WITH_DRAFT_EAGER = YES
DRAFT_WINDOW_GRAPH_REQUIRED_FOR_EAGER_FEATURE_DELIVERY = NO
```

This spike explores Draft Window Graph startup capture only. It does not alter
the already usable Target-graph + Draft-eager delivery path.

## 3. Existing integration architecture

The worker patch
`vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py` already installs:

```text
upstream dflash.cudagraph.build_attn_metadata
  = vllm_ascend.worker.v2.attn_utils.build_attn_metadata

upstream dflash.speculator.DFlashCudaGraphManager
  = vllm_ascend.worker.v2.spec_decode.dflash.aclgraph.DFlashAclGraphManager
```

It also carries the independent DFlash2 selector-kernel patch. The project
patch policy permits a minimal necessary worker patch, requires a removal plan,
and requires UT plus eventual E2E evidence. The installation is a one-time
worker-startup symbol replacement, not a mutable per-capture swap.

`IS_PATCH_ARCHITECTURE_AN_EXISTING_MRV2_INTEGRATION_MECHANISM = YES`

## 4. Exact capture chain

```text
AscendDFlashSpeculator / AscendDSparkSpeculator
  -> DraftModelSpeculator owns self.input_buffers
  -> DFlashAclGraphManager.capture(..., self.input_buffers, ...)
  -> upstream DFlashCudaGraphManager.capture
  -> create_forward_fn(BatchExecutionDescriptor)
  -> module helper _prepare_dflash_inputs_to_capture
  -> InputBatch.make_dummy
  -> canonical BlockTables.get_dummy_block_tables
  -> canonical BlockTables.get_dummy_slot_mappings
  -> build_attn_metadata (already patched to Ascend)
  -> AttentionState(metadata, full slot mappings)
  -> Draft model capture
```

The helper already passes block tables, sequence lengths, and slot mappings as
separate builder inputs. Therefore Draft read table/length can be changed while
the full slot/write carrier stays canonical.

## 5. Exact runtime chain and frozen ordering

```text
prepare_dflash_inputs(full)
  -> full positions/query state
  -> full slot mapping and physical KV write
  -> P6 Draft-private graph metadata
  -> REPLAY
  -> actual graph consumer
  -> CONSUMER observation
  -> update_full_graph_params
  -> backend.update_graph_params
  -> UPDATE observation
```

The spike does not change `run_fullgraph()` or
`update_full_graph_params()`. The static order remains:

```text
metadata rebuild -> REPLAY -> CONSUMER -> UPDATE
```

Static source does not prove whether `UPDATE(N)` affects replay `N`, replay
`N+1`, or another task launch. `NEEDS_NPU_TIMELINE` remains open.

## 6. P6 blocker, stated precisely

P6 already supplied:

- capture identity separate from request generation;
- per-consumer persistent graph backing;
- runtime generation and mapping-epoch validation;
- Draft-private metadata and Target isolation;
- backend attribution and update binding;
- replay/update timeline status.

The missing arrow was:

```text
P6 persistent startup carrier
  -X-> pinned upstream DFlash capture helper
```

The pinned helper selected its own dummy full read inputs and had no
instance-owned carrier parameter. The local source spike closes only that
metadata-construction seam by patching the existing module helper symbol.

## 7. Draft `InputBuffers` ownership proof

Pinned `DraftModelSpeculator.__init__()` allocates a fresh
`self.input_buffers = InputBuffers(...)`. `set_attn()` stores Target buffers in
the distinct `self.target_input_buffers`. DFlash/DSpark capture passes
`self.input_buffers` to its query graph manager.

The POC validates both identities before attaching context:

```text
capture_input_buffers is speculator.input_buffers
capture_input_buffers is not speculator.target_input_buffers
```

The context exists only inside the manager's `try/finally` capture scope and is
removed on success and exception. Two fake speculators use distinct contexts
and distinct persistent carrier addresses.

`DRAFT_INPUT_BUFFERS_INSTANCE_PRIVATE = PROVEN`

## 8. Descriptor-to-carrier mapping

Before entering upstream capture, the manager sees its exact
`_capture_descs`. The typed context maps each descriptor to an already
registered P6 capture identity by:

```text
(num_reqs, num_tokens, effective descriptor mode)
```

and verifies the full serialized descriptor:

```text
mode, reqs, tokens, uniform width, max query, LoRA count, ubatches
```

The helper receives `num_reqs`, `num_tokens`, and `skip_attn` and resolves
exactly one mapping. Zero matches, duplicate matches, stale descriptor, wrong
bucket, wrong route, wrong backing, foreign owner, and runtime-bound generation
all hard fail.

The current characterized DFlash/DSpark route uses effective `FULL`
descriptors. PIECEWISE remains unsupported as a product route; its helper
skip-attention behavior is covered defensively.

## 9. Selected source seam

The POC adds the same-signature adapter:

```text
cudagraph_module._prepare_dflash_inputs_to_capture
  = ascend_prepare_dflash_inputs_to_capture
```

Behavior:

```text
no explicit context
  -> call the saved exact original helper
  -> existing Ascend builder patch remains in effect

explicit typed context
  -> build baseline dummy InputBatch
  -> obtain canonical dummy full tables and full slot mapping
  -> resolve P6 persistent read carrier
  -> seed capture backing at its stable address
  -> call Ascend builder with Window read table and read lengths
  -> keep full slot mapping, query layout, and positions owner
  -> return upstream-compatible AttentionState
```

No new `build_attn_metadata` parameter was needed. Existing independent
parameters are sufficient.

The saved original helper is immutable patch configuration, not mutable runtime
transport. Runtime state lives only on the Draft-private `InputBuffers` object.

## 10. Frozen read/write boundary

| State | Capture POC source | Changed by Window? |
|---|---|---:|
| Draft read block table | P6 persistent carrier | yes |
| Draft device exact | P6 persistent carrier | yes |
| Draft CPU exact/upper | P6 persistent carrier | yes |
| valid block count | P6 persistent carrier | yes |
| slot mapping | canonical full `BlockTables` | no |
| query start/layout | baseline dummy `InputBatch` | no |
| positions owner | Draft baseline `InputBuffers` | no |
| canonical FullSource | read-only to Window adapter | no |
| Target metadata/history | not used as transport | no |
| physical KV write | full/absolute | no |

The upstream dummy helper intentionally initializes its own persistent dummy
rows. The Window adapter adds no canonical-source mutation; a regression test
uses observable non-zero source contents and verifies they remain unchanged.

## 11. Capture initialization versus runtime semantics

Capture identity must not manufacture a request, generation, mapping epoch, or
request fingerprint. The startup path therefore seeds only capture geometry:

```text
capture_upper = min(max_model_len, W + block_span_tokens - 1)
valid_blocks  = ceil(capture_upper / block_span_tokens)
```

This value is not a claim about a real request. Runtime P6 binding later copies
the real P3 generation into the same persistent addresses. Actual operator
capture and refresh require NPU evidence.

## 12. Backend and topology limits

| Backend/route | Local conclusion |
|---|---|
| dense GQA/FIA direct-prefix DFlash | POC candidate |
| eligible DSpark on same route | POC candidate |
| Eagle3 | not covered by this helper |
| DSA / DSA-CP | blocked; separate SAS/SWA and derived state |
| SFA / indexer | blocked; separate derived buffers |
| MLA | blocked; backend-specific metadata/update |
| recycling/native | blocked; no typed graph resident-set contract |

P6 fingerprint constraints remain unchanged: TP=DP=PP=PCP=DCP=1, no SP,
DSA-CP, FlashComm, async, or prefix cache. These are characterization guards,
not a proof that broader topology is impossible. TP16 is not proven.

## 13. Alternatives adjudicated

| Alternative | Verdict | Reason |
|---|---|---|
| patch existing helper + existing builder patch + instance carrier | selected for local POC | smallest explicit Ascend-owned seam |
| modify upstream helper signature | rejected | violates R-REPO-01 |
| copy entire capture assembly | rejected | unnecessary drift surface |
| builder-only patch | rejected | cannot select an instance carrier |
| ContextVar/module global registry | forbidden | hidden cross-instance state |
| per-capture temporary function swap | forbidden | shared mutable module state |

## 14. Source changes in the local spike

| File | Change |
|---|---|
| `vllm_ascend/worker/v2/spec_decode/dflash/capture.py` | typed scope, descriptor mapping, same-signature adapter, capture seeding |
| `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py` | scopes explicit context around existing upstream capture only |
| `vllm_ascend/worker/v2/spec_decode/draft_window_graph.py` | exposes registered capture identities and stable startup read inputs |
| `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py` | installs helper symbol once |
| `vllm_ascend/patch/__init__.py` | patch rationale and removal plan |
| `tests/ut/spec_decode/test_draft_window_graph_carrier.py` | A–Q capture-seam contracts |

Commit stat: 6 files, 937 insertions, 33 deletions.

## 15. Test evidence

Red-before-green:

```text
ModuleNotFoundError:
No module named 'vllm_ascend.worker.v2.spec_decode.dflash.capture'
```

Final local results:

| Command/scope | Result | Interpretation |
|---|---|---|
| P5/P6 graph binding + carrier | 83 passed | PASS |
| full `tests/ut/spec_decode` | 635 passed, 13 skipped, 7 failed | not PASS; 7 host failures below |
| unmodified baseline full spec_decode | 621 passed, 13 skipped, same 7 failed | exact failure parity; POC adds 14 passing cases |
| attn_utils/attention/DFlash/DSpark/DFlash2/Eagle graph selections | 174 passed, 2 subtests passed | PASS |
| ACL graph host tests | 24 passed, 3 failed, 2 subtests passed | not PASS; exact baseline parity |
| Ruff check / format check | pass | PASS |
| targeted Mypy | pass | PASS |
| compileall / diff-check | pass | PASS |

The seven spec_decode failures all originate at pinned vLLM
`vllm/v1/attention/selector.py:208` with `Invalid attention backend for None`
while constructing VWN Eagle3 models on a host without a selected NPU backend.
No POC file appears in those stacks. The three ACL graph failures similarly
originate from `current_platform.graph_pool_handle=None` and reproduce on the
unmodified `1b7215c` baseline. These are recorded as environment failures, not
as passing tests.

## 16. Final source adjudication

```text
PATCH_HELPER_ROUTE = FEASIBLE
LOCAL_GRAPH_CAPTURE_SEAM_POC = PASS
NPU_GRAPH = NOT RUN / NOT VERIFIED
TP16_GRAPH = NOT PROVEN
PUBLIC_GRAPH_SUPPORT = STILL FROZEN
```

The source spike proves that an instance-owned persistent carrier can reach
the Ascend metadata builder at startup capture while full slot/write state is
preserved. It does not prove that ACL Graph captured those addresses, that the
NPU operator reads the intended physical set, or that replay/update timing is
correct.

