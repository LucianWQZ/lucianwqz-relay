# P7-X Graph DSA and DSA-CP Design

## Status

This is a source-closed implementation blueprint. DSA and DSA-CP Graph Window are not enabled. They require separate derived-carrier adapters above the common P6 provider because their operators do not consume the FIA table/length pair directly.

```text
GRAPH_DSA_DESIGN: READY WITH DSA-SPECIFIC DERIVED ADAPTER
GRAPH_DSACP_DESIGN: READY WITH GLOBAL-TO-LOCAL DERIVED BANK
NPU: NOT RUN
PUBLIC GRAPH SUPPORT: FROZEN
```

## Shared Frozen Contract

The logical Window plan remains global and absolute. Only Draft read visibility and read-derived state may change. Canonical full block tables, absolute positions, query layout, slot mapping, physical KV writes, Target metadata, and Target cache remain unchanged.

The common P6 generation/provider/identity is reused. DSA adds backend-derived operands; it does not create a second policy or source plane.

## DSA Source Ownership

Primary files and owners:

- `vllm_ascend/attention/dsa_v1.py::AscendDSAMetadataBuilder`
- `vllm_ascend/attention/dsa_v1.py::AscendDSAMetadataBuilder.build_for_drafting`
- `vllm_ascend/attention/dsa_v1.py::AscendDSAMetadataBuilder.build_req_metadata_for_drafting`
- `vllm_ascend/attention/dsa_v1.py::AscendDSAImpl.update_graph_params`
- `vllm_ascend/worker/v2/attn_utils.py::build_attn_metadata`

The builder owns persistent or capacity-bound state including `spec_sas_metadata` and `dspark_swa_indices_buffer`. `AscendDSAImpl.update_graph_params` is effectively a no-op for these operands. Consequently, DSA cannot rely on the FIA task-rebind behavior used by the base candidate.

## DSA Dataflow

```text
P1 global WindowPlan [S,E)
-> P2 canonical FullSource + valid counts
-> P3 generation-bound Window table/exact/upper
-> DSA draft metadata builder
-> SAS metadata
-> SWA/index buffers and formatted read state
-> captured DSA operator operands
```

The Window table and length are necessary but not sufficient. Every derived tensor that is captured by address must be owned by a descriptor/consumer-specific stable bank and refreshed before replay.

## DSA Carrier Schema

Minimum typed state:

- common capture identity and runtime generation identity;
- gid and DSA backend/builder identity;
- descriptor, bucket, padded row/token geometry;
- stable Window table/exact/upper backing;
- stable SAS metadata backing;
- stable `dspark_swa_indices_buffer` backing;
- any formatted slot/index/read-length operands actually consumed by the DSA kernel;
- derived-state generation and source fingerprint;
- completion owner preventing overwrite.

All derived buffers must match the same generation. A correct table paired with stale SAS/index state is a hard failure.

## Capture / Runtime / Update

### Capture

Register every actual DSA operand address, not just the common block table. Capture identity includes backend class, builder class, gid, descriptor, geometry, device/dtype/shape, and consumer ordinal.

### Runtime

1. validate P3 generation and source identity;
2. materialize Window from canonical FullSource;
3. invoke DSA builder logic against the Window read view while preserving full write inputs;
4. copy all derived results into persistent capture-owned buffers;
5. validate table/length/SAS/index generation equality;
6. replay;
7. hold buffers until true consumer completion.

### Update

Because the backend update is not the carrier, pre-replay in-place refresh and stream ordering are mandatory. UPDATE may record attribution but cannot be treated as the moment that makes the current replay correct.

## DSA Fail-closed Conditions

- no stable derived buffer owner;
- capacity or shape mismatch;
- SAS/index/table generation mismatch;
- unknown consumer ordinal;
- compressor or QLI semantics not represented;
- source residency unavailable;
- graph completion/lifetime unavailable;
- any slot/Target alias;
- unsupported topology or group composition.

## DSA Red Tests

- captured addresses stable while SAS/index contents change A/B/A';
- stale SAS with fresh Window table is rejected;
- stale SWA indices with fresh exact length is rejected;
- derived buffer aliasing canonical source/workspace/Target is rejected;
- capacity pressure fails deterministically;
- full slot mapping and positions remain identical to OFF;
- no-op backend UPDATE cannot be accepted as proof of refresh;
- source shortage and invalid resident set fail before replay.

## DSA NPU Oracle

Collect actual operator operand addresses and values for Window OFF/ON and A/B/A'. Compare CPU Window oracle, SAS/index derivation, physical read set, Draft output, full slot/write, Target metadata/logits, and stream completion. A host metadata match alone is insufficient.

## DSA-CP Source Ownership

Primary files and owners:

- `vllm_ascend/attention/context_parallel/dsa_cp.py::AscendDSACPMetadataBuilder`
- `vllm_ascend/attention/context_parallel/dsa_cp.py::AscendDSACPMetadataBuilder.build_for_drafting`
- `vllm_ascend/attention/context_parallel/dsa_cp.py::AscendDSACPMetadataBuilder.build_req_metadata_for_drafting`
- `vllm_ascend/attention/context_parallel/dsa_cp.py::_build_local_token_metadata`
- `vllm_ascend/attention/context_parallel/dsa_cp.py::AscendDSACPImpl`

The logical Window plan must not be divided by CP world size. Projection occurs in the DSA-CP builder using actual rank ownership and block geometry.

## DSA-CP Projection Contract

```text
global absolute [S,E)
-> validate one global proposal/generation
-> local_prefix(rank,E) - local_prefix(rank,S)
-> rank-local query/seq state
-> rank-local SAS/index/rope/derived buffers
-> rank-local captured operator
```

The union of rank-local visible positions must equal the global logical Window after native/resident filtering. `V / cp_world_size` is forbidden.

## DSA-CP Persistent Bank

The carrier bank key must include:

- capture descriptor and consumer ordinal;
- CP rank/world size and ownership scheme;
- global gid and backend/builder identity;
- block geometry and padded layout;
- proposal generation and mapping epoch at runtime;
- local query, sequence, SAS, index, RoPE, and any communication operands;
- provider schema version.

One global generation owns all rank-local entries. Partial-rank publication is rejected.

## DSA-CP Capture / Runtime / Update

Capture registers each rank's stable local operands. Runtime first validates the global plan, then projects locally and refreshes each rank's derived bank. A barrier/atomic submission contract prevents one rank from replaying generation N while another remains on N-1. Slot/write stays bound to the full physical owner.

## DSA-CP Fail-closed Conditions

- rank/world/topology mismatch;
- missing rank or duplicate rank;
- local projection does not union to the global interval;
- cross-group or cross-generation cache reuse;
- stale local SAS/index/sequence state;
- communication stream/completion owner unresolved;
- DSA-CP plus unsupported SP/FlashComm/prefix combination;
- full slot/write cannot be independently proven.

## DSA-CP Red Tests

- exhaustive small global intervals versus rank-local projection oracle;
- exact boundary and non-boundary cases;
- different block geometries;
- rank mismatch and partial-rank bind;
- stale local state while global generation advances;
- multi-gid generation mismatch;
- full slot identity/content unchanged;
- previous Window never used as source;
- completion of one rank cannot release all ranks early.

## DSA-CP NPU Oracle

For every CP rank record global S/E, local visible positions, table/index/SAS operands, actual physical reads, slot/write, communication ordering, and completion. The global union must equal the CPU oracle exactly, with no duplicate/missing logical positions outside native semantics.

## Implementation Order

1. close base G1–G5 on NPU;
2. implement DSA stable derived bank and host tests;
3. NPU-characterize DSA operands/read set;
4. implement DSA-CP global-to-local projection bank;
5. NPU-characterize all ranks and lifecycle;
6. only then consider a product capability gate.

DSA and DSA-CP may share identity/provider infrastructure, but they may not reuse the FIA metadata adapter as if their derived operands were task-rebound.

