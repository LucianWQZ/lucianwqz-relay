# P7-E Eager Topology Fingerprint Specification

## Status and purpose

This specification describes review-final `P7EagerTopologyFingerprint` at
vLLM-Ascend commit `4753742ab181920292c504a79eedecf9b428ae1b`
(original P7 commit `7feb6def...`). It is a local eager identity contract, not a
support declaration and not a Graph route fingerprint.

The fingerprint prevents an admitted single-group/TP1 eager generation from being
reused by a different method, backend, group, topology, mode, or execution lane.

## Schema

| Field | Producer | Meaning | Validation / consumer |
|---|---|---|---|
| `normalized_method` | P1/P2 inventory | normalized method policy identity | non-empty lowercase; generation identity |
| `runtime_route` | concrete speculator route | DFlash/DSpark/Eagle3/DFlash2-style path identity | non-empty lowercase; async pool and capability decision |
| `attention_backend_family` | immutable hardware profile | semantic `STANDARD` versus `COMPATIBILITY` implementation family | typed enum; only `STANDARD` may pass current P7-E capability gate |
| `backend_impls` | P2 executable attention groups | fully qualified actual backend classes | same cardinality/order as gids |
| `builder_impls` | P2 groups | fully qualified metadata builder classes | detects builder drift/mismatch |
| `global_group_ids` | P2 inventory | global gid for each executable group | nonnegative and ordered |
| `layouts` | P2 classification | dense/DSA/SFA/MLA/native category | complex layouts fail closed |
| `block_geometry` | P2 groups | `(gid, logical B, kernel B)` | same cardinality/order as gids |
| `tensor_parallel_size` | `ParallelConfig` | TP world | only 1 admitted now |
| `data_parallel_size` | `ParallelConfig` | DP world | only 1 admitted now |
| `pipeline_parallel_size` | `ParallelConfig` | PP world | only 1 admitted now |
| `prefill_context_parallel_size` | `ParallelConfig` | PCP world | only 1 admitted now |
| `decode_context_parallel_size` | config plus BlockTables CP | effective DCP world | only 1 admitted now |
| `sequence_parallel` | runtime config | SP mode | false admitted now |
| `dsa_context_parallel` | runtime config | DSA-CP mode | false admitted now |
| `flashcomm` | config/environment-derived mode | FlashComm execution mode | false admitted; never transports Window state |
| `graph_mode` | effective Draft graph mode | `NONE`/FULL/FULL_DECODE_ONLY/PIECEWISE | only `NONE` admitted |
| `async_scheduling` | scheduler config | async execution request | true is host-only `STATIC_READY` |
| `prefix_caching` | cache config | prefix-cache participation | true fails closed |
| `provider_version` | P3 runtime schema | provider/identity schema | strictly positive |
| `execution_lane` | runtime/pool owner | stable lane that owns backing | nonnegative; exact match required |

## Construction and propagation

```text
P2 inventory + runtime context
  → _build_topology_fingerprint()
  → P7EagerCapabilityDecision
  → require_live_materialization()
  → DraftWindowSourceCapability.eager_topology_fingerprint
  → DraftWindowRuntimeState.topology_fingerprint
  → DraftWindowGenerationIdentity.topology_fingerprint
  → DraftMetadataInputs / async handle validation
```

`CONFIG_OFF` and `FORCED_OFF` decisions contain no topology fingerprint and create
no source/workspace/lease. Rejected eligible routes may have a diagnostic
fingerprint, but `require_live_materialization()` prevents it entering P2/P3 state.

## Equality and lane rules

- Equality is exact dataclass equality; there is no subset or wildcard match.
- `DraftWindowRuntimeState` validates exact equality before initial materialize,
  serialized refresh, and active-input consumption; the fingerprint is not merely
  diagnostic state.
- `for_execution_lane()` returns a new immutable instance.
- The lane in the fingerprint must equal the P3 identity and pool lane.
- Changing async mode or lane creates a different fingerprint.
- Method names, class names, gids, layouts, and geometry are ordered; a reordered
  group set is not the same topology.
- Environment variables may influence a mode bit such as FlashComm but never carry
  generation, request, table, or length state.

## Route decisions

The fingerprint is an identity, not an allowlist. Admission still requires the
capability evaluator to return `READY_FOR_NPU`. In particular:

- Graph mode mismatch fails closed;
- async returns `STATIC_READY` and cannot materialize live state;
- any parallel dimension outside the exact route fails closed;
- homogeneous multi-group fails closed;
- heterogeneous multi-group is owner blocked;
- complex layouts fail closed;
- prefix caching fails closed.

## DCP projection seam

P7 adds a pure mathematical result type, `DCPWindowIntervalProjection`, for future
topology work. Given canonical global `[S,E)`:

```text
local_start = local_prefix(S, rank)
local_end   = local_prefix(E, rank)
local_V     = local_end - local_start
```

This handles interleaving and non-divisible boundaries. It expressly rejects the
incorrect shortcut `V / dcp_world_size`. No rank-local block table, metadata,
operator binding, or NPU evidence exists, so DCP remains `FAIL_CLOSED`.

## Invariants

1. Fingerprint construction does not allocate Window state.
2. It never contains Target metadata, slot mapping, positions, request identity,
   generation id, or mapping epoch; those remain in their existing typed owners.
3. A runtime generation carries both its generation identity and topology identity.
4. A topology mismatch is a hard failure; it is never normalized or rebound.
5. Graph Track remains independent and frozen.

## Independent Review Resolution

DeepSeek F-01 was `PARTIALLY_ACCEPTED`: platform identity was missing, but current
310P non-MTP reachability was disproved by its model-runner/model-state gates. The
semantic hardware-family field and `STANDARD`-only admission are now part of the
fingerprint. F-03 was `ACCEPTED`: a same-source topology-drift regression first
showed the serialized runtime did not enforce the recorded value; the three runtime
validation boundaries above now fail before workspace write or consume.

```text
TOPOLOGY SCHEMA: FINAL FOR P7-E STATIC CONTRACT
RUNTIME ENFORCEMENT: PASS
GRAPH TRACK: FROZEN
NPU TOPOLOGY EVIDENCE: NOT VERIFIED
```

