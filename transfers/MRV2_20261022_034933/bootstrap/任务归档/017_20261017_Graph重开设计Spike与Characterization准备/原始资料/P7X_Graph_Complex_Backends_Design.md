# P7-X Graph Complex Backends and Multi-group Design

## Executive Status

The common Graph Window provider/identity layer is reusable, but complex backends require schema-specific carrier adapters. None of the routes in this document is enabled by the base characterization candidate.

| Route | Architecture compatibility | Missing Graph-specific contract | Current status |
|---|---|---|---|
| SFA main | Compatible with separate adapter | stable main metadata/derived operand bank | fail closed |
| SFA indexer | Compatible with separate adapter | independently attributed indexer carrier | fail closed |
| QLI/compressed indexer | Compatible with separate adapter | cache/source version and top-k/index operands | fail closed |
| MLA | Compatible with MLA adapter | decode schema mapping and task-update proof | fail closed |
| Homogeneous multi-group | Compatible | N per-gid atomic carrier bank | fail closed |
| Heterogeneous multi-group | Compatible in principle | adapter for every backend plus atomic generation | owner blocked/fail closed |
| DFlash2 | No current method Graph owner | baseline method-level Graph implementation | fail closed |

## SFA Main Attention

### Exact owners

- `vllm_ascend/attention/sfa_v1.py::AscendSFAMetadataBuilder`
- `vllm_ascend/attention/sfa_v1.py::AscendSFAMetadataBuilder.build_for_drafting`
- `vllm_ascend/attention/sfa_v1.py::AscendSFAImpl`
- `vllm_ascend/attention/sfa_v1.py::AscendSFAImpl.update_graph_params`
- CP variants in `vllm_ascend/attention/context_parallel/sfa_cp.py`

SFA metadata is not FIA metadata. Its main attention path carries backend-specific sequence/index/NoPE state. The update method is not a proven FIA-style Window carrier; source review shows direct-captured/derived semantics that require persistent operands.

### Required adapter

- consume common P3 Window generation and absolute visibility;
- build SFA-specific per-token visible counts and translated indices;
- preserve absolute positions and full write slot mapping;
- bind a stable per-descriptor main-attention operand bank;
- tag every derived tensor with generation, gid, backend/builder, and consumer ordinal;
- refresh before replay and retain until true completion.

### Red tests

- per-token visibility and index translation oracle;
- stale main buffer with fresh table rejection;
- NoPE/main length mismatch rejection;
- Target/full-slot storage isolation;
- address-stable A/B/A';
- update no-op cannot masquerade as current-generation binding.

## SFA Indexer, QLI, and Compressed Cache

### Exact owners

- `vllm_ascend/attention/indexer.py::AscendSFAIndexerMetadataBuilder`
- `vllm_ascend/attention/indexer.py::AscendSFAIndexerBackend`
- `vllm_ascend/attention/indexer_kpool.py::AscendIndexerKPoolMetadataBuilder`
- `vllm_ascend/attention/indexer_kpool.py::AscendIndexerKPoolTailMetadataBuilder`
- `vllm_ascend/models/deepseek_v4/indexer.py::DeepseekV4Indexer`
- `vllm_ascend/models/deepseek_v4/indexer.py::AscendIndexerOps`

The indexer is a distinct cache layer/consumer. It owns its own cache-write slot mapping and read/top-k metadata. That write mapping is not the Draft attention slot mapping and cannot be inferred from the common FIA carrier. Main SFA and indexer consumers must be independently attributed while belonging to the same proposal generation.

### Missing state

- main/indexer consumer ordinal and dependency order;
- stable top-k indices, group lengths, key/cache indices, RoPE tables, and QLI scale/key carrier where applicable;
- indexer cache/source version and resident epoch;
- compression ratio/layout/schema version;
- per-consumer completion owner;
- proof that a refreshed main carrier cannot pair with stale indexer state.

### Required behavior

```text
one logical generation
  -> SFA main derived bank
  -> indexer/QLI derived bank
  -> validate both banks
  -> replay consumers in the source-defined order
  -> retire only after all consumers complete
```

Any un-attributed indexer, QLI, k-pool, or tail-cache consumer causes fail closed.

### NPU oracle

Capture actual main and indexer operand addresses, source versions, top-k outputs, physical reads, Draft outputs, Target outputs, and completion order. Correct main attention alone is insufficient.

## MLA

### Exact owners

- `vllm_ascend/attention/mla_v1.py::AscendMLAMetadataBuilder`
- `vllm_ascend/attention/mla_v1.py::AscendMLAImpl.update_graph_params`
- CP variants under `vllm_ascend/attention/context_parallel/mla_cp.py`
- common entry `vllm_ascend/worker/v2/attn_utils.py::build_attn_metadata`

### Why FIA cannot be inherited

MLA has different metadata classes, decode table fields, sequence/upper/padding semantics, chunk/prefill variants, and actual operator operands. A class-name compatibility check is not enough. The adapter must map the Window read view into the concrete MLA decode schema and then verify the backend task update consumes it.

### Required adapter and tests

- typed MLA capture identity including schema/layout/PCP-DCP mode;
- persistent MLA decode table and sequence carriers;
- exact/upper/padded-row validation;
- attribution of every operand read by the MLA operator;
- Task-rebound versus direct-captured classification from the actual backend path;
- OFF parity, Target isolation, stale generation, schema drift, D2H accounting, and A/B/A tests.

Prefill/chunk, PCP/DCP, or NoPE variants remain fail closed until their own schema and operator are proven.

## Multi-group

### Current source fact

`vllm_ascend/worker/v2/attn_utils.py::build_attn_metadata` iterates cache groups, while P2/P6 currently allow only a single executable direct-prefix group for Window. Multi-group therefore cannot be obtained by cloning the single carrier.

### Correct contract

```text
one logical generation and absolute [S,E)
  -> gid 0 source/provider/projection/carrier/consumer(s)
  -> gid 1 source/provider/projection/carrier/consumer(s)
  -> ...
  -> atomic all-gid validation and submission
```

Each gid owns its own:

- block geometry and valid counts;
- backend/builder identity;
- source owner/version;
- capture descriptor and consumer ordinals;
- table/exact/upper/derived buffer backing;
- completion accounting.

The anchor is never recomputed using an LCM and the result of one gid is never used as another gid's source.

### Homogeneous groups

May reuse one backend adapter with N independent carriers. Required tests include two different physical tables with the same absolute Window, partial bind rejection, no shallow tensor alias, and atomic retirement.

### Heterogeneous groups

Require an adapter for every participating backend. FIA+MLA or FIA+DSA cannot submit until all consumers are attributed and all carriers carry the same generation. This remains owner blocked where the legacy heterogeneous group contract is unresolved.

### NPU oracle

For every gid and consumer record actual operands and physical reads. Verify all project the same logical `[S,E)` under their native visibility and that full slot/write/Target state remains unchanged.

## DFlash2

### Exact owner

`vllm_ascend/worker/v2/spec_decode/dflash2/speculator.py::init_cudagraph_manager`

Current source rejects/non-supports the method's Graph route and does not instantiate the DFlash Graph manager/capture consumer. There is therefore no legal carrier endpoint. Reusing the DFlash helper based on method ancestry would bypass DFlash2 selector/operator semantics.

### Prerequisite

DFlash2 first needs a baseline method-level Graph contract, manager, descriptor, metadata consumer, update/lifetime behavior, and NPU baseline evidence. Only after that exists can the common provider core be attached through a DFlash2-specific adapter.

Current tests should only prove that DFlash2 cannot be accidentally enabled by the base candidate.

## Shared Versus Separate Components

Reusable across all routes:

- policy and public fail-closed gate;
- generation/mapping/request identity;
- capture/runtime namespace separation;
- provider schema and route fingerprint framework;
- persistent ownership/lifetime invariants;
- source spy event vocabulary;
- canonical source and full write invariants.

Not reusable as-is:

- FIA metadata adapter;
- FIA task-rebind assumption;
- one-consumer carrier layout;
- single-gid retirement;
- DFlash capture entry for Eagle3 or DFlash2;
- DSA/SFA/MLA derived tensor schemas.

## Implementation and Campaign Order

After base G1–G5 closes, MLA can be implemented independently from DSA. SFA main/indexer should be one coordinated workstream. Multi-group should follow at least two stable single-group adapters, because otherwise partial-generation failures cannot be meaningfully tested. DFlash2 is blocked on a separate method Graph prerequisite.

