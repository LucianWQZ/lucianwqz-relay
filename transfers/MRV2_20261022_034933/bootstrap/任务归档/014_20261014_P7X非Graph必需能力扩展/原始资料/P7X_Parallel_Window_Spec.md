# P7-X Parallel Window Specification

## Contract

Window planning uses one logical absolute interval `[S,E)` per request. A
topology provider determines whether the read carrier is replicated or needs a
backend-specific projection. It never changes absolute positions or write slots.

`P7EagerTopologyFingerprint` includes method, route, backend/builders, gids,
layout, block geometry, TP/DP/PP/PCP/DCP, SP, DSA-CP, FlashComm, async, prefix,
provider version, lane, TP rank and parallel-read semantics. Drift is rejected
before publish/forward.

It deliberately does **not** duplicate W or K/query width. Topology identity is
not proposal/window identity. W is bound through policy, WindowPlan, read
descriptors and generation; K/query width is bound through the provider's
expected future offset and method-specific materialization plan. Runtime
artifacts must still record W/K explicitly.

## Ordinary TP

Current source gives every process its local `BlockTables` object with the same
logical request sequence. Therefore P7-X uses `parallel_read_semantics =
replicated` for ordinary TP:

```text
global [S,E)
  -> identical logical descriptor on every TP rank
  -> process-local canonical FullSource
  -> process-local Window workspace
  -> process-local Draft consumer
```

TP rank is resolved from an explicit test/config field or the initialized TP
group. TP>1 without a resolvable rank fails; rank zero is never guessed. TP2,
TP4 and TP16 geometry tests prove rank identity and reject mismatch. No table
or visible length is divided by TP world size.

## DCP and DSA-CP

DCP's mathematical projection remains:

```text
local_visible = local_prefix(E) - local_prefix(S)
```

not `(E-S)/world_size`. DCP live support remains Report1-dependent.

DSA-CP is a backend-derived route. The common Window table/exact length enters
the actual `AscendDSACPMetadataBuilder`; the builder owns local ranges, local
lengths, indices and communication state. P7-X does not invent a second CP
projection or mutate the full slot map.

## Other topology states

| Topology | Status | Missing fact |
|---|---|---|
| ordinary TP1/2/4/16 | `LOCAL_STATIC_READY` | NPU per-rank operand/slot/output proof |
| DSA-CP, uncompressed single group | `LOCAL_STATIC_READY` | NPU local derived metadata and communication proof |
| DP, PP, PCP, DCP, SP | `REPORT1_RUNTIME_DEPENDENT` | runtime carrier/projection authority |
| FlashComm outside proven DSA-CP route | `REPORT1_RUNTIME_DEPENDENT` | comm buffer/stream/lifetime owner |
| any Graph mode | `GRAPH_FROZEN` | intentionally outside P7-X |

## Invariants and tests

- same canonical S across ranks and groups;
- per-rank topology identity cannot be forged or drift after materialization;
- request/mapping/generation identities remain rank-local and explicit;
- full slot mapping and canonical table are unchanged;
- source shortage, invalid rank and unsupported stacking fail before allocation.

Actual TP16, DSA-CP and communication correctness remains a Node101 NPU Gate.
