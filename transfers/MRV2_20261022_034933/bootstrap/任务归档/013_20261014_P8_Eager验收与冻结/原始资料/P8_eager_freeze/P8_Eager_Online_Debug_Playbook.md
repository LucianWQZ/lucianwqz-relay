# MRV2 Draft Sliding Window — P8-E Online Debug Playbook

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

Debug in this fixed order and stop at the first divergence. Instrumentation must be
observation-only, separately committed, disabled by default, and never merged into
the delivery lineage unless independently reviewed as production code.

## 1. Policy

- Source: `worker/v2/spec_decode/__init__.py::init_speculator` and
  `draft_window.py::resolve_draft_window_policy`.
- Expect: one of CONFIG_OFF, FORCED_OFF, or ELIGIBLE_ON; forced-OFF occurs before
  numeric validation.
- Inspect: requested/effective W, normalized method/model, reason, warning count.
- First divergence: wrong method/model normalization or receiver/factory parity.
- Likely bugs: special MTP missed, V4 DSpark predicate drift, plain Eagle leak.
- Forbidden workaround: silently turn an eligible route OFF or bypass policy.
- Cleanup: confirm no inventory/workspace/provider exists after OFF/forced-OFF.

## 2. P7 capability and hardware family

- Source: `draft_window_eager_capability.py::evaluate_draft_window_eager_capability`.
- Expect: exact positive route returns READY_FOR_NPU; Graph/prefix/parallel/complex
  backends fail closed; async returns STATIC_READY; COMPATIBILITY fails closed.
- Inspect: status, reason, backend family and complete topology fingerprint.
- First divergence: a route is overclassified before any source allocation.
- Likely bugs: class inheritance erases platform identity, runtime flag omitted.
- Forbidden workaround: force READY or remove the preallocation gate.
- Cleanup: rejected route has zero FullSource/workspace/P7 pool/Graph provider.

## 3. Topology fingerprint

- Source: `P7EagerTopologyFingerprint`, `build_draft_window_source_capability`,
  `DraftWindowRuntimeState` validation.
- Expect: exact method/route/backend/builder/gid/layout/geometry/world sizes/flags/
  lane/provider version; exact equality before materialize, refresh and consume.
- Inspect: immutable serialized representation and generation-carried copy.
- First divergence: admitted fingerprint differs from runtime or active generation.
- Likely bugs: lane drift, environment-derived FlashComm mismatch, stale topology.
- Forbidden workaround: wildcard/subset comparison or rebinding an active identity.
- Cleanup: abort generation; never reuse backing after mismatch.

## 4. P2 inventory

- Source: `draft_window.py::build_draft_window_inventory` and
  `build_draft_window_source_capability`.
- Expect: one executable global gid, `FullAttentionSpec`, exact Ascend FIA backend
  and builder, dense direct-prefix layout, supported geometry.
- Inspect: global gid, class identities, logical/kernel B, capability failures.
- First divergence: actual Draft consumer differs from assumed model/backend.
- Likely bugs: target backend mistaken for Draft backend, DFlash2 inheritance,
  hidden multi-group or complex consumer.
- Forbidden workaround: guess from model name or discard a group.
- Cleanup: rejection before canonical source binding.

## 5. Canonical FullSource

- Source: `FullDraftKVSource` and `bind_batch`.
- Expect: borrowed, read-only canonical full tables/counts; current idx_mapping maps
  batch rows to persistent rows; block id 0 remains valid.
- Inspect: owner identity, storage pointer, shape/dtype, valid counts, source version.
- First divergence: alias/owner changes, stale persistent-row mapping, source shortage.
- Likely bugs: pointer used as freshness, tail counted from block values, clone owner.
- Forbidden workaround: mutate/replace full table or infer valid counts from zeroes.
- Cleanup: invalidate generation; preserve canonical owner/content.

## 6. WindowPlan and descriptor

- Source: `compute_draft_window_scalar_plan`, `SingleGroupDirectPrefixProvider`.
- Expect: method-correct H; canonical floor-aligned S; exact E; V=E−S under the
  frozen interval contract; source columns fit valid count.
- Inspect: L0/K/H/S/E/V, B, first offset, required columns, capacity.
- First divergence: off-by-one, S recomputed per Eagle3 step, source shortage.
- Likely bugs: upper used as exact, K/K+1 confusion, per-gid realignment.
- Forbidden workaround: clamp silently, align S again, window a previous Window.
- Cleanup: fail before workspace write.

## 7. P3 lease/workspace

- Source: `DraftWindowRuntimeState::materialize`, workspace and lease pool.
- Expect: strictly increasing mapping_epoch, ordered request fingerprint, one active
  owner, stable address, deterministic active/tail writes, no canonical alias.
- Inspect: generation id, epoch, requests, phase/step/lane, state, backing pointers.
- First divergence: stale/ABA identity, active backing overwritten, wrong tail.
- Likely bugs: same tensor rewritten without epoch, wrong retirement owner.
- Forbidden workaround: blind round-robin, per-call owner replacement, forced retire.
- Cleanup: use the owning abort/retire path; preserve pending reader ownership.

## 8. Typed DraftMetadataInputs

- Source: `DraftMetadataInputs::validate_for` and the method-specific single
  validation boundary.
- Expect: table, valid count, device exact, CPU exact and upper share generation;
  active/padded rows agree; no positions, slots or Target state are transported.
- Inspect: identity, tensor addresses, shapes/dtypes, exact/upper relations.
- First divergence: stale expected identity or mixed-generation tensor.
- Likely bugs: bypassed validation, host/device values sourced separately.
- Forbidden workaround: manual validation at multiple call sites or global transport.
- Cleanup: abort generation before builder.

## 9. DraftMetadataStore

- Source: `DraftMetadataStore`, `publish_metadata`, `read_metadata`.
- Expect: Draft-private root and nested mutable storage; publish receives real,
  nonempty Target metadata only for isolation audit; stale read fails.
- Inspect: root ids, nested Tensor/NumPy storage, owner generation and store state.
- First divergence: Target alias, active overwrite, stale generation read.
- Likely bugs: filtered Target metadata mutated in place, fake `{}` Target.
- Forbidden workaround: use `model_state.attn_metadata` as Draft transport.
- Cleanup: reset/abort through P3 owner; verify Target identity/content unchanged.

## 10. P4 method consumer

### DFlash / eligible DSpark

- Source: `draft_window_eager.py`, DFlash/DSpark `set_attn` and `propose`.
- Expect: pure-prefill baseline bypass; mixed hard reject before epoch; DFlash K+1,
  DSpark K or K+1; one materialize/validate/build/forward/retire sequence.
- Inspect: proposal fingerprint, epoch, actual query width and read inputs.

### Eagle3

- Source: `draft_window_eagle3.py` and AR speculator `_prefill`,
  `_multi_step_decode`, `_build_draft_attn_metadata`, `_generate_draft`.
- Expect: static K; L0 pre-rejection; H=L0+K; proposal-frozen S; Draft-private first
  pass; each E_s refreshes directly from FullSource; step retires before refresh.
- Inspect: proposal id, step, L0/H/S/E/V, future columns, rejection correction.

For both, forbidden workarounds are reusing Target metadata, changing slot/position,
or suppressing unsupported-route exceptions.

## 11. Backend metadata

- Source: `draft_window_eager.py::_build_ascend_draft_attn_metadata`, AR
  `_build_eagle3_private_attn_metadata`, and `attn_utils.py::build_attn_metadata`.
- Expect: only Draft read block table and read length differ from baseline; query
  starts, positions, causality, layer mapping and full slot mapping remain legal.
- Inspect: builder class, kwargs, exact/upper, padded rows, metadata storage aliases.
- First divergence: field parity or FIA carrier differs for a reason beyond Window.
- Forbidden workaround: copy entire speculator/builder or use deprecated upstream
  CPU length fields.

## 12. Actual operator

- Source: `attention/attention_v1.py::_get_fia_params`,
  `forward_fused_infer_attention`, `full_graph_fia*` (Graph calls are observation
  references only; Eager route remains the subject).
- Expect: Draft operator gets Window table and exact KV lengths; Target operator gets
  full table/lengths; q lengths and full physical slots remain baseline.
- Inspect: complete table pointer/content, actual sequence lengths, layer identity,
  Draft-vs-Target attribution and kernel/profiler evidence level.
- First divergence: metadata correct but actual operand wrong.
- Forbidden workaround: infer physical read solely from Python object equality.

## 13. Full slot mapping and physical KV write

- Source: `worker/v2/block_table.py::BlockTables.compute_slot_mappings` (and the
  pinned upstream block-table contract),
  `attention/attention_v1.py::AscendAttentionBackendImpl.reshape_and_cache`, and
  the NZ writer `AscendC8AttentionBackendImpl::_reshape_and_cache`.
- Expect: slot mapping is computed from the canonical full block table and absolute
  positions, is byte/value-equal OFF versus ON, and remains independent of the Draft
  Window read table. The standard writer passes it to
  `DeviceOperator.reshape_and_cache`; the NZ writer passes it to
  `torch_npu.npu_scatter_pa_kv_cache`. `notify_kv_cache_written()` occurs only after
  the canonical write call.
- Inspect: untruncated full table row, absolute position, logical/kernel block size,
  independently recomputed physical slot, metadata `slot_mapping`, writer/operator
  argument, request row and generation. Compare every active token, not only the
  first/last slot.
- First divergence: (a) independent full-table/position oracle versus
  `metadata.slot_mapping`, or (b) metadata slot versus the actual KV-write operand.
  Either is a write-side correctness failure even if Draft outputs appear valid.
- Likely bugs: Window table accidentally used for slot calculation, truncated or
  padded row treated as active, request reorder/row reuse paired with a stale full
  row, CP projection applied twice, or Draft/Target writer attribution confused.
- Forbidden workaround: derive slots from the Window table, override slots in Draft
  metadata, mutate canonical/Target owners, accept output equality as a slot oracle,
  or treat `_get_fia_params` (a read-carrier path) as proof of KV-write correctness.
- Cleanup: stop the disposable service, preserve full table/positions/slot/operator
  artifacts, verify Target and canonical owners were not mutated, then retire only
  through the owning generation path.

## 14. Stream/completion and retirement

- Source: method forward completion and `DraftWindowRuntimeState` retirement.
- Expect: serialized eager consumer has completed before backing reuse; generation
  identity advances; exceptions release through one owner.
- Inspect: stream, event/timestamp, generation/backing addresses, retire/reuse order.
- First divergence: overwrite before consumer completion or leaked active lease.
- Forbidden workaround: add an unconditional global synchronize and call it proof;
  fake host events do not establish NPU safety.
- Cleanup: stop service on uncertain ownership; do not reuse backing.

## 15. First-divergence report template

```text
case / machine / device / SHAs
first failing layer (1-14)
expected typed state
actual typed state
generation / mapping_epoch / requests / topology / gid / phase / step / lane
table and length identities
Target/write before/after
operator/event evidence level
cleanup performed
raw artifact paths and hashes
```

## Frozen Graph Track Appendix

Graph modes remain rejected and the P6 provider has no production installation
point. Do not debug an Eager failure by enabling P5/P6 Graph provider, changing
capture, adding a ContextVar/global, swapping Target owners, or applying the old
upstream prototype. Graph resumes only after an owner-authorized seam decision.
