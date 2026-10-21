# P7-X Graph Patch Feasibility Study

## Decision status

`PATCH_HELPER_ROUTE = FEASIBLE_FOR_LOCAL_STATIC_POC`

This is not a support decision. It authorizes only a local, instance-scoped
proof of the startup metadata carrier seam. Product Graph Window modes remain
fail closed and all device claims remain open.

## 1. Exact source

| Repository | SHA | Tree | State |
|---|---|---|---|
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | clean, read-only |
| vLLM-Ascend | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` | clean spike parent |

## 2. Existing patch system

`patch_dflash_speculator.py` already patches two upstream DFlash integration
symbols: the metadata builder and graph-manager class. The worker patch
lifecycle installs them once during worker initialization. Project policy says
patches are temporary, should be minimal, need a removal plan, and require UT
and E2E evidence. Therefore patching the neighboring private helper is an
existing MRV2 integration mechanism, but only as the smallest repository-bound
seam and not as a permanent public API.

`IS_PATCH_ARCHITECTURE_AN_EXISTING_MRV2_INTEGRATION_MECHANISM = YES`

Future removal plan: replace the private-symbol patch when upstream exposes an
explicit vendor-neutral capture read-input provider or when repository policy
permits such a hook.

## 3. Exact blocker in P6

P6 already owns capture identities, stable per-consumer carrier backing,
runtime generation binding, Draft-private metadata, Target/write isolation,
backend attribution, and replay/update validation. Its missing arrow is:

```text
registered persistent capture carrier
  -X-> upstream _prepare_dflash_inputs_to_capture
```

`observe_draft_window_graph_capture()` therefore rejects provider-present
startup capture. It is not a replay/update-carrier defect.

`CAPTURE_CARRIER_INJECTION_BLOCKER`: upstream's module-global helper selects
dummy full read operands, while Ascend previously patched only the builder and
manager symbols; no instance-owned context reached that helper.

## 4. Draft `input_buffers` ownership

Pinned `DraftModelSpeculator.__init__` creates a fresh `InputBuffers` instance
per speculator. `set_attn()` stores Target buffers in a distinct
`target_input_buffers` attribute. DFlash capture passes `self.input_buffers`.
The class has no slots and no process/module registry.

Consequently a typed context attached under `try/finally` to this exact Draft
instance is:

- instance-scoped;
- accessible to the helper through its existing signature;
- separate across engines/speculators;
- not Target state;
- removable on success and exception.

`DRAFT_INPUT_BUFFERS_INSTANCE_PRIVATE = PROVEN`

## 5. Context transport candidates

| Candidate | Draft-private | Helper-visible | Multi-instance | Mutates shared owner | Verdict |
|---|---:|---:|---:|---:|---|
| Draft `input_buffers` instance | yes | yes | yes | no | preferred |
| `model_state` | no; Target-oriented | no direct parameter | risky | yes/ambiguous | reject |
| canonical `block_tables` | shared full owner | yes | shared | yes | reject |
| `attn_groups` | shared capability descriptors | yes | not transport-owned | yes/ambiguous | reject |
| manager instance | yes | not in helper signature | yes | no | needs extra hidden registry/signature change |
| module global / ContextVar | no | yes | unsafe | global hidden state | forbidden |

## 6. Descriptor-to-carrier mapping

The helper receives `num_reqs`, `num_tokens`, and `skip_attn`. The typed context
is built before `super().capture()` from already registered P6 capture
identities and indexes them by:

```text
(padded_request_count, padded_token_count, effective_descriptor_mode)
```

where mode is `FULL` when `skip_attn=False` and `PIECEWISE` otherwise. Current
DFlash/DSpark capture produces `FULL` decode descriptors; DFlash does not
support PIECEWISE. Any zero match, duplicate match, wrong route, wrong bucket,
wrong backing identity, or stale context fails closed. This is unique in the
current single-lane scope and deliberately rejects future ambiguous modes.

## 7. Metadata-builder compatibility

Ascend `build_attn_metadata` already accepts independent:

- device `seq_lens`;
- per-group `block_tables`;
- per-group `slot_mappings`;
- CPU exact and upper lengths;
- query-start carriers;
- capture mode.

No new builder parameter is needed. The POC can pass persistent Window table
and exact/upper lengths while preserving dummy full slot mappings and baseline
query geometry.

`CAN_METADATA_BUILDER_CONSUME = YES`

## 8. Persistent capture contents

P6 capture registration allocates stable carrier addresses but initializes
contents to zero and intentionally has no request generation. At capture, the
adapter may seed those same stable buffers from the helper's canonical dummy
inputs:

- table: direct-prefix slice of the full dummy table, copied into carrier
  backing;
- exact/upper: deterministic dummy capture capacity bounded by
  `min(max_model_len, window_size + block_span_tokens - 1)`; this seeds
  capture geometry only and is not a real request-visible length;
- valid counts: deterministic direct-prefix count;
- slot mapping: always rebuilt from canonical full `BlockTables`.

This is capture-shape initialization, not a fake request generation. Runtime
P6 binding later refreshes the same addresses from a real P3 generation.

## 9. Backend-derived-state matrix

| Backend | Capture read source | Derived state | Stable/rebind evidence | Spike status |
|---|---|---|---|---|
| FIA / dense GQA direct-prefix | common metadata table/length | standard FIA metadata | P6 exact `AscendAttentionBackendImpl` update attribution | POC candidate |
| DSA / DSA-CP | DSA builder plus SAS/SWA indices | `spec_sas_metadata`, DSpark SWA indices, CP projections | separate persistent and update paths | blocked, independent inventory required |
| SFA / indexer | SFA/MLA-common plus indexer metadata | indexer/compressed buffers | separate builder/update contracts | blocked |
| MLA | MLA common metadata and derived buffers | backend-specific graph params | separate update implementation | blocked |
| recycling/native variants | resident/provider-specific | backend-owned derived state | no P6 typed graph contract | blocked |

The helper patch does not generalize backend support. Existing P6 inventory and
fingerprint gates remain authoritative.

## 10. Topology scope

The current fingerprint rejects TP/DP/PP/PCP/DCP values other than one and
rejects SP, DSA-CP, FlashComm, async, and prefix caching. These are
characterization-scope guards backed by absent per-rank capture evidence, not a
claim of fundamental impossibility. They remain unchanged. TP16 eager evidence
does not prove TP16 Draft Graph.

## 11. Replay/update protocol

No POC change is allowed in `run_fullgraph()` or
`update_full_graph_params()`. The source order remains metadata rebuild,
REPLAY, CONSUMER, UPDATE. `NEEDS_NPU_TIMELINE` remains open.

## 12. Alternatives

Scoring: 5 is best; forbidden options are marked reject.

| Option | Repo boundary | Isolation | Capture coverage | Replay risk | Drift | Testability | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| P0 helper patch + existing builder patch + instance carrier | 5 | 5 | 4 | 5 | 3 | 5 | selected POC |
| P1 change upstream helper signature | 0 | 5 | 5 | 5 | 5 | 5 | forbidden by R-REPO-01 |
| P2 copy/override capture assembly | 5 | 4 | 5 | 3 | 1 | 4 | larger than necessary |
| P3 builder-only patch | 5 | 1 | 2 | 5 | 3 | 2 | lacks instance carrier selection |
| P4 ContextVar/global | 5 | 0 | 4 | 2 | 3 | 1 | forbidden |

## 13. POC admission gates

| Gate | Evidence | Result |
|---|---|---|
| A Draft input owner safe | fresh `InputBuffers` per speculator; Target stored separately | pass |
| B helper resolves carrier | typed instance context + unique bucket/mode key; ambiguity rejects | pass |
| C full slot/write preserved | slot mapping remains derived from canonical `BlockTables` | pass |
| D Window read reaches builder | builder has independent table/length parameters | pass |
| E OFF exact baseline | no context delegates to saved original helper | pass |
| F replay/update unchanged | POC touches capture manager/helper only | pass |
| G pinned vLLM unchanged | worker startup symbol patch only | pass |
| H no global/ContextVar | context lives only on Draft `input_buffers` | pass |
| I P6 provider reused | capture identity/read carrier/backing remain P6-owned | pass |

## 14. Recommendation

Implement a local POC with:

1. a small DFlash capture adapter with the exact upstream helper signature;
2. an explicit typed context scoped to Draft-private `input_buffers`;
3. P6 provider APIs to resolve registered capture carriers without exposing a
   request generation;
4. one-time worker symbol installation while preserving the saved original
   helper for OFF delegation;
5. unit tests for symbol install, OFF parity, read/write split, identity,
   cleanup, ambiguity/staleness, skip-attention, and zero allocation.

The POC must not install a production provider automatically, remove the
Graph product gate, alter public support matrices, or claim NPU capture.

