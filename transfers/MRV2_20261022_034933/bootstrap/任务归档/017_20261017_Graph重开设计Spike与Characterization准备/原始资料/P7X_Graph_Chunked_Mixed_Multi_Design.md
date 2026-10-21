# P7-X Graph Chunked / Mixed / Multi-request Design

## Status and Boundary

This document is an implementation-ready design, not a support claim. The base Graph characterization candidate does not enable chunked prefill, mixed prefill/decode, or general multi-request Graph Window execution. The public Graph Window gate remains fail closed.

The existing eager/non-Graph work already provides row identity, phase classification, generation, `mapping_epoch`, canonical `FullSource`, and safe materialization. The remaining work here is the Graph-specific composition of those contracts.

Frozen invariants:

- only Draft read table/read length/derived read state may change;
- slot mapping, absolute positions, query layout, physical KV writes, Target metadata, and canonical full tables remain full and unchanged;
- replay order remains `metadata rebuild -> REPLAY -> CONSUMER -> UPDATE`;
- capture fixes storage geometry, not request identity;
- no module global, `ContextVar`, owner swap, or vLLM modification.

## Source Facts

The relevant existing owners are:

- `vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py::classify_draft_window_batch_phase`
- `vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py::build_phase_aware_materialization_plan`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py::_draft_window_proposal_scope`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py::DraftWindowProposalEpochSource`
- `vllm_ascend/worker/v2/spec_decode/draft_window.py::DraftWindowGenerationIdentity`
- `vllm_ascend/worker/v2/spec_decode/draft_window_graph.py::_validate_runtime_capture_compatibility`
- `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py::DFlashAclGraphManager.run_fullgraph`

Pinned vLLM selects the DFlash/DSpark proposal and Graph descriptor. Ascend must not reinterpret a prefill row as a decode row merely to match an existing descriptor.

## Chunked Prefill

### Current owner

The phase classifier has enough information to distinguish continuing chunked prefill, terminal prefill, and decode. The eager path safely preserves baseline behavior for prefill phases and refreshes source state before later decode proposals.

### Graph-specific contract

`FULL_DECODE_ONLY` does not authorize applying a decode capture bucket to a chunked-prefill row. The intended first implementation is:

```text
continuing chunk
    -> baseline/non-Window legal path
    -> update canonical full state and request epoch
terminal chunk
    -> baseline/non-Window legal path
next decode proposal
    -> new runtime generation
    -> fresh FullSource/resident snapshot
    -> Graph Window bind
```

If source inspection or NPU trace proves that a chunk itself enters the Draft query Graph, it needs a dedicated phase-qualified capture descriptor. It may not borrow the decode descriptor.

### Required typed state

- row phase (`CONTINUING_PREFILL`, `TERMINAL_PREFILL`, `DECODE`);
- proposal/batch epoch;
- capture mode and descriptor bucket;
- actual query width and padded geometry;
- ordered request fingerprint;
- mapping epoch;
- source/residency version produced after the last chunk.

### Exact implementation seams

- extend the Graph route fingerprint in `draft_window_graph.py` with phase/bucket compatibility;
- derive phase only in `draft_window_nongraph.py`, never from a local variable name;
- validate before provider bind in `dflash/aclgraph.py::run_fullgraph`;
- keep `draft_window_graph_characterization.py` observational until NPU evidence establishes the phase route.

### Red tests

1. continuing chunk presented to a decode descriptor is rejected before carrier bind;
2. terminal chunk cannot reuse an earlier decode generation;
3. decode after multiple chunks observes the final canonical source version;
4. no Window workspace/provider state is created for a bypassed chunk;
5. stale residency or mapping epoch fails before replay;
6. full slot/positions/query remain unchanged through chunk-to-decode transition.

### NPU oracle

Use one prompt spanning multiple chunks. Record every chunk phase and then the first decode proposal. The first Graph read table must match the post-final-chunk `FullSource`, while slot/write and Target metadata match Window OFF.

**GRAPH_CHUNKED_PREFILL_DESIGN: READY, NPU ROUTE CLASSIFICATION REQUIRED.**

## Mixed Prefill / Decode

### Product decision still required

A batch with request A decoding and request B prefilling cannot silently use a homogeneous decode capture bucket. Three contracts are technically possible:

1. a dedicated mixed FULL descriptor and row-mask-aware metadata schema;
2. split execution into phase-homogeneous submissions;
3. an explicit safe eager fallback before any Graph state is acquired.

The current owner has not selected one. Therefore this design does not implement or enable mixed Graph execution.

### Required state if supported

- per-row phase and active mask;
- per-row actual/padded query width;
- mixed descriptor schema/version;
- per-row exact/upper read lengths;
- consumer row mask and output merge order;
- one generation identity covering the whole submitted batch;
- explicit fallback/split reason when the descriptor is unavailable.

### Exact seams

- `draft_window_nongraph.py::classify_draft_window_batch_phase`
- `draft_window_eager.py::_draft_window_proposal_scope`
- descriptor selection in the pinned vLLM DFlash/DSpark manager (read-only dependency)
- Ascend validation before `DFlashAclGraphManager.run_fullgraph`
- a future Ascend-owned mixed adapter; no existing owner currently satisfies this contract.

### Fail-closed behavior

- mixed phase without an owner-approved contract is rejected before carrier/materialization/replay;
- no mid-replay `NotImplementedError` may terminate EngineCore;
- no decode-only descriptor may accept prefill rows;
- an explicit eager fallback, if later approved, must be selected before acquiring Graph resources.

### Red tests

- decode + continuing prefill;
- decode + terminal prefill;
- mixed row reorder;
- one row finish plus one new prefill arrival;
- descriptor/bucket mismatch;
- fallback creates no Graph Window state;
- partial row masks cannot publish a carrier.

**GRAPH_MIXED_DESIGN: ARCHITECTURALLY READY; OWNER CONTRACT REQUIRED.**

## Multi-request Lifecycle

### Storage versus row meaning

Capture may bind a stable padded backing address. It must never bind semantic request identities to capture row numbers. Runtime row meaning is dynamic:

```text
stable backing address
    + mutable active contents
    + generation identity
    + monotonic mapping_epoch
    + ordered request fingerprint
```

### Runtime sequence

```text
snapshot ordered req_ids and idx_mapping
-> begin generation/mapping epoch
-> bind canonical source for active rows
-> reset inactive tail/padding
-> materialize read carrier
-> validate capture/runtime fingerprint
-> publish all rows atomically
-> replay/consume
-> completion and retire
```

Reorder, finish/add, and same-row replacement all create a new generation. Semantic A/B/A' may reuse the same address, but A' is not generation A.

### Required state

- ordered request fingerprint, not only row indices;
- actual and padded row count;
- active-row mask;
- mapping epoch;
- source owner/version;
- descriptor/bucket and route fingerprint;
- per-gid carrier set when multi-group is introduced;
- completion owner preventing early overwrite.

### Exact seams

- `draft_window.py::DraftWindowGenerationIdentity`
- `draft_window_eager.py::DraftWindowProposalEpochSource`
- `draft_window_graph.py::DraftWindowGraphBindingProvider`
- `draft_window_graph.py::_validate_runtime_capture_compatibility`
- `draft_window_graph_characterization.py::prepare_parallel_draft_window_graph_runtime`

### Red tests

- `[A,B] -> [C,A] -> [A,B']`;
- finish/add without pointer change;
- same persistent row reused by a new request;
- in-place `idx_mapping` rewrite with pointer unchanged;
- ABA stale handle;
- active-row tail not reset;
- one row or gid bound from the next generation while others remain old;
- early overwrite while consumer completion is pending;
- padded bucket changes without a compatible capture identity.

### NPU oracle

Run batch > 1 pure decode, then finish/add, reorder, and real row reuse. For each replay collect request order, generation, mapping epoch, carrier address/content, physical read set, full slot/write, and completion order.

**GRAPH_MULTI_REQUEST_DESIGN: READY; RUNTIME/NPU EVIDENCE REQUIRED.**

## Combined Dependency and Risk

Chunked prefill and multi-request identity can be developed after G1–G5 because they reuse the base provider. Mixed serving additionally needs an owner-selected execution policy. Prefix residency, if enabled, becomes another generation-bound source version and must be coordinated with these transitions.

The highest-risk failure is not a wrong Python value but a semantically stale captured carrier whose address remains valid. Every transition therefore validates identity and source version before replay, not after UPDATE.

