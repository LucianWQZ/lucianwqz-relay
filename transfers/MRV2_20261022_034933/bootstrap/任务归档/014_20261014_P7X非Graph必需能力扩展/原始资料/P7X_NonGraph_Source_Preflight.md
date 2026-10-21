# P7-X Non-Graph Source Preflight

## Status and exact baseline

- Date: 2026-10-14 (Asia/Shanghai)
- vLLM: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`, tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`, clean and read-only.
- vLLM-Ascend parent: `4753742ab181920292c504a79eedecf9b428ae1b`, tree `b7e525c3c9d45617ad1023ad45c6948c466a3631`.
- Development branch: `feature/p7x-nongraph-completion`.
- Repository rule: production changes are restricted to vllm-ascend. Graph remains frozen at P6/P6A.

This preflight was produced from the exact checkout before P7-X production edits. It records source facts, not NPU support claims.

## Existing P1-P7 data path

```text
factory policy
  -> build_draft_window_source_capability()
  -> P2 inventory + canonical FullDraftKVSource
  -> SingleGroupDirectPrefixProvider
  -> DraftWindowRuntimeState / stable workspace / lease / store
  -> P4 method-specific eager materialization
  -> AscendDraftAttentionReadInputs
  -> Ascend build_attn_metadata()
  -> backend metadata builder
```

The independent write path remains:

```text
canonical BlockTables + absolute positions
  -> full slot_mappings
  -> KV write
```

P7-X must generalize the read plane without swapping or mutating that owner.

## TP and parallel source facts

1. `BlockTables.input_block_tables`, persistent `num_blocks`, `idx_mapping`, and request order are local worker objects. Ordinary TP does not split the logical block-table row in the speculator path. Each process owns its own speculator/runtime and sees the same logical request interval. Therefore ordinary TP read semantics are replicated, not `V / tp_world_size`.
2. The existing P7 gate rejects every `tensor_parallel_size != 1` before FullSource creation. No missing table-sharding operation was found for ordinary FIA; that gate is conservative for dense FIA TP.
3. DCP is different. The pinned code projects prefixes using interleaving; the already-tested formula is `local(E) - local(S)`, never `V / world_size`.
4. DSA-CP is also different. `AscendDSACPMetadataBuilder` obtains real TP group rank/world geometry and builds local query/sequence and sparse-index metadata from `AscendCommonAttentionMetadata`. It must consume Window common metadata and remain responsible for its own derived state.
5. PCP, PP, DP, SP, and FlashComm have separate ownership/communication paths. This preflight found no source proof that they are required by the mandatory GLM/Qwen route. They remain explicit Report1/runtime dependencies unless a P7-X provider closes them.
6. Slot mappings in the P4 vendor-local builder always come from `self.block_tables.slot_mappings`; P7-X must preserve this on all ranks.

## DSA and DSA-CP source facts

- `AscendDSAMetadataBuilder.build_for_drafting()` consumes `common_attn_metadata.block_table_tensor`, `seq_lens`, absolute positions, and full slot mapping.
- It rejects compressed drafting (`compressor_ratio > 1`). The source-safe local candidate is the uncompressed/SWA drafting path only.
- DSpark SWA indices are derived by the backend from the common read table and lengths. Feeding an already-windowed common read carrier therefore composes Draft visibility with native SWA inside the backend instead of scalar-min approximation.
- `AscendDSACPMetadataBuilder.build_for_drafting()` and `build_req_metadata_for_drafting()` likewise derive local metadata and sparse indices from the common carrier. The builder, not the Window planner, owns DSA-CP derived buffers and communication metadata.
- Compressor/QLI, SFA/indexer, MLA, and recycling/native circular layouts have different operands. No safe generic direct-prefix consumer contract was proved for them in this checkout.

## Async source facts

- `draft_window_async.py` already owns a bounded fixed-capacity lane pool and a complete host state machine, but P7 Final deliberately has no production installation point.
- A production-safe completion token can wrap a real `torch.npu.Event`: record after Draft consumer submission, query without blocking, retain the workspace and backend-derived buffers until complete, then retire/release.
- Sleep, Python object identity, and proposal-return are not completion proofs.
- Eagle3 performs several Draft forwards per proposal and rewrites Window state per step. Each in-flight step must own distinct backing or be retired only after a real completion token; a one-lane serialized overwrite is not an async contract.
- Host/fake-event tests can prove state transitions and pressure only. Stream ordering remains an NPU gate.

## Prefix-cache and residency source facts

- Prefix sharing/hits are reflected in canonical physical block IDs. Active resident extent is represented by persistent per-request `num_blocks` gathered through the same `idx_mapping` used for the batch.
- FullSource validates owner identity and replacement; request identity + mapping epoch detects reorder, finish/add, and row reuse.
- A source-safe prefix resident-set contract can therefore use the canonical FullSource plus per-gid valid counts. It must revalidate at materialization and must reject a requested interval beyond the resident extent.
- The Window table remains a read view. Full slot mapping continues to be computed from the canonical table and absolute positions.
- Runtime eviction while a Draft reader is in flight still requires lease/event evidence and remains in the NPU campaign.

## Chunked-prefill and mixed-batch source facts

Pinned `InputBatch` provides:

- `num_computed_prefill_tokens_np`: state before the current target step;
- `num_scheduled_tokens`: this target step's row width;
- `prefill_len_np`: prompt length;
- `is_prefilling_np`: `computed < prefill_len` before this step;
- request IDs and `idx_mapping` in the same ordered batch rows.

The exact row classification is:

```text
computed >= prefill_len                       -> PURE_DECODE
computed < prefill_len and computed+scheduled < prefill_len
                                                -> PREFILL_CONTINUING
computed < prefill_len and computed+scheduled >= prefill_len
                                                -> PREFILL_TERMINAL
```

Current P4 code bypasses an all-prefill batch and raises for a mixed prefill/decode batch. That whole-batch policy is the mandatory gap.

For a source-safe mixed carrier:

- continuing-prefill rows retain the full canonical read interval for that step;
- terminal/decode rows use the method-specific Window interval;
- all rows retain baseline query layout, absolute positions, and full slot mapping;
- one ordered row-phase fingerprint belongs to the proposal generation;
- no decode row silently falls back because another row is prefill.

The first proposal after terminal prefill remains method-specific. Eagle3 still needs proposal-frozen `S`; DFlash uses K+1; eligible DSpark uses its actual K/K+1 query width.

## Multi-request source facts

`DraftWindowProposalEpochSource` already provides a caller-owned monotonic mapping epoch and fingerprints both ordered request IDs and mapping contents. P3 identities reject stale generations. The missing P7-X contract is row phase/residency/topology as part of the same immutable identity and row-wise materialization for mixed batches.

## Multi-group source facts

- `build_attn_metadata()` already iterates every KV cache group and accepts one block table per global gid.
- Current P2 inventory scans every executable consumer, but intentionally records multi-group as a failure and `DraftWindowSourceCapability` retains one provider/runtime.
- Safe homogeneous generalization is one canonical absolute anchor with a provider and valid-count gather per gid under one proposal identity. Each output table is built from that gid's canonical FullSource row.
- Heterogeneous groups additionally need per-layout native/resident providers. No repeated-window or LCM anchor is allowed.
- Multiple executable consumers sharing one gid remain ambiguous and source-blocked unless the backend exposes one unambiguous read carrier.

## Backend/provider inventory

| Layout | Actual source consumer | Local source conclusion |
|---|---|---|
| Dense GQA/FIA | `AscendAttentionMetadataBuilder` consumes common table/length | Existing reference carrier; ordinary TP is replicated |
| DSA-v1 uncompressed/SWA | `AscendDSAMetadataBuilder.build_for_drafting()` derives sparse/native state from common table/length | Typed backend-derived provider is source-safe; NPU pending |
| DSA-CP uncompressed/SWA | `AscendDSACPMetadataBuilder.build_for_drafting()` derives local metadata/indices | Source-safe provider boundary; rank/stream behavior NPU pending |
| DSA compressor/QLI | builder asserts drafting ratio <= 1 | `SOURCE_BLOCKED` for current P7-X |
| SFA/indexer | separate per-token/index operands and persistent buffers | `REPORT1_RUNTIME_DEPENDENT`/`SOURCE_BLOCKED` until actual required consumer is known |
| MLA | distinct exact/upper and operator operand contract | `REPORT1_RUNTIME_DEPENDENT` |
| native/circular/recycling/offload | resident set may have gaps and reuse | `SOURCE_BLOCKED` absent a typed resident-set provider |

## GLM/Qwen facts

- No source-only proof identifies the exact GLM-5.2-W4A8 Draft backend/model composition in this checkout. The requested DSpark K8 TP16 route can be architecture-ready through the generic method/topology/provider contracts, but its actual group/layout remains a Report1 assumption.
- Existing Qwen test fixtures exercise dense Eagle3/DFlash/DSpark carriers. These are local architecture candidates, not current-SHA NPU evidence.

## Safe implementation seams selected for P7-X

1. Add an Ascend-owned non-Graph contract module for row phase, residency, topology, backend provider decisions, and multi-group bundle validation.
2. Replace the whole-batch prefill gate with an immutable row-phase plan and row-wise read descriptors.
3. Permit prefix cache only through the canonical resident-count provider; no flag-only enablement.
4. Permit ordinary replicated TP for proven providers while keeping DCP/SP/PCP/PP/DP/FlashComm explicit.
5. Extend backend classification only for uncompressed DSA/DSA-CP source contracts; leave other layouts closed with exact reasons.
6. Integrate the existing async pool only where a real event factory and per-operation backing are installed; retain static-only status if live source wiring cannot be proven without NPU/runtime facts.
7. Keep Graph gates and P5/P6 provider installation unchanged.

## Source drift

- Historical documents described all prefill as a terminal bypass and all parallel/complex backends as fail-closed. The exact checkout exposes enough per-row phase data and DSA drafting builders to refine those conclusions for the P7-X non-Graph scope.
- No source drift changes the Frozen Window math, read/write separation, forced-OFF policy, or repository boundary.

## Pre-code gate

The following can proceed to red tests: row phase/mixed serving, canonical prefix residency, ordinary replicated TP identity, uncompressed DSA/DSA-CP provider selection, multi-request lifecycle, and homogeneous per-gid contract.

Async NPU completion, actual GLM backend identity, compressed DSA/SFA/MLA/recycling consumers, and heterogeneous required-route identity remain explicit Report1/NPU dependencies; they must not be guessed.
