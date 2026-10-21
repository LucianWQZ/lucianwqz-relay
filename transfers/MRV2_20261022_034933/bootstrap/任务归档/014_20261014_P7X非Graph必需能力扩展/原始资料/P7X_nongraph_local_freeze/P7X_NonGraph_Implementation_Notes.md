# P7-X Non-Graph Mandatory Completion — Implementation Notes

## 1. Exact state

```text
vLLM baseline: 84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM tree: f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
vLLM-Ascend parent: 4753742ab181920292c504a79eedecf9b428ae1b
P7-X commit: 7e88db6ed31e7965f526ea6f49cc17101f4a65b4
P7-X tree: 71800e2e250f0b4dc51aede643eebff55e39b404
P7-X review-fix: c1c2129aa49ee1de381130729de73124a6ec893a
P7-X final tree: 384af8a0466f6aea2e73d6217f9802415b5ccd40
branch: feature/p7x-nongraph-completion
review status: adjudicated; local freeze verified
NPU status: not verified
```

## 2. Why P7-X exists

P8 froze a safe first eager candidate but deliberately rejected TP>1, async,
prefix cache, mixed/chunked proposals, complex backends and multi-group routes.
The 2026-10-14 owner amendment makes the non-Graph workstreams mandatory.
P7-X extends the existing read plane; it does not change Window math or create
a second transport.

## 3. End-to-end data flow

```text
P1 policy/math
  -> P2 inventory + canonical FullSource
  -> P7-X backend/topology/phase decision (before allocation)
  -> P3 generation + mapping_epoch + workspace/lease/store
  -> resident snapshot + row-aware descriptors
  -> P4a DFlash/DSpark or P4b Eagle3 metadata consumer
  -> eager Draft attention
  -> optional async completion event
  -> retire/reuse
```

The independent write path stays:

```text
Scheduler/BlockTables -> absolute positions -> full slot_mapping -> physical KV write
Target model_state.attn_metadata -> full Target read
```

## 4. File map

| File | Main change | Why |
|---|---|---|
| `draft_window_nongraph.py` | phase plans, resident snapshots, backend-provider kinds, capability decision | one typed admission layer before FullSource/workspace |
| `draft_window.py` | TP rank, source geometry facts, DSA ratio, explicit uncompressed DSA source, row-phase identity, full-width workspace | preserve canonical ownership while admitting safe new routes |
| `draft_window_eager_capability.py` | TP rank and parallel read semantics in topology fingerprint | reject topology drift and distinguish replicated/DCP/DSA-CP semantics |
| `draft_window_eager.py` | row-aware materialization, prefix snapshot, live async lane lifecycle | mixed/chunked/prefix/async DFlash/DSpark production path |
| `draft_window_eagle3.py` | phase-aware first pass/steps while freezing S | mixed/terminal rows without window-of-window |
| `draft_window_async.py` | real event adapter, same-epoch continuation rules, metadata retention, nonblocking reclaim | prevent backing or derived metadata reuse before device completion |
| `attn_utils.py` | DSA-CP builder receives common request metadata | real backend builder contract, not a model-name guess |
| six test files | red-to-green contracts and regression | external behavior and lifetime proof |

## 5. Phase-aware read semantics

Each proposal binds immutable ordered request IDs, `idx_mapping`, and a row phase:

- `PREFILL_CONTINUING`: current resident full prefix, `S=0` for that row;
- `PREFILL_TERMINAL`: normal Window plan for the transition proposal;
- `PURE_DECODE`: normal Window plan.

An all-continuing batch bypasses Window state entirely and follows baseline. A
mixed batch does not bypass: all rows share one stable full-width workspace,
but each row copies only the columns described by its own descriptor. Padded
rows/tails are zeroed on every materialization.

## 6. Prefix/current canonical extent

`DraftWindowResidentSetSnapshot` binds gid, ordered request IDs, mapping
fingerprint, FullSource identity and a cloned valid-count snapshot. The count is
the allocated/current canonical valid extent, not a universal physical
residency oracle. The actual table is always copied from canonical FullSource
at materialization time. This supports current prefix sharing and eviction/reuse
semantics without treating block ID zero as a sentinel or deriving slots from
the Window table.

The currently admitted dense/uncompressed DSA/DSA-CP paths have no separate
offload residency layer in source. Future SFA, offload, recycling, or circular
routes must provide a real resident-set provider rather than reusing this name.

## 7. Parallel and TP

Ordinary TP is classified as replicated read semantics. Every rank has its
own immutable fingerprint containing world size and resolved rank, while S/E/V
remain logical/global sequence facts. No `V / tp_world_size` is performed.
DCP remains a separate interleaved projection contract. DSA-CP is admitted
only when the actual group builder is `AscendDSACPMetadataBuilder` and the DSA
cache is uncompressed; its builder derives local metadata from the common
Window table/length.

## 8. Backend providers

The source-safe live provider set is deliberately narrow:

- dense FIA direct-prefix;
- DSA native/SWA with actual compression ratio 0 or 1;
- DSA-CP native/SWA with ratio 0 or 1.

Compressed DSA/QLI is rejected. SFA/MLA/native recycling and unknown builders
remain runtime/source gated. Multi-group has a canonical-S design but no live
P3/P4 bundled carrier, so it is not allocated.

## 9. Async lifecycle

For eligible DFlash/DSpark async eager execution:

```text
FREE -> ACQUIRED -> MATERIALIZED -> BOUND -> SUBMITTED
     -> CONSUMER_COMPLETE -> RETIRED -> FREE
```

Each pool lane owns an independent P3 runtime/workspace. The handle retains the
complete Draft-private metadata and explicit backend-derived tensors through
completion. Production records a `torch.npu.Event` on the current stream. The
optional integer `additional_config.draft_window_async_lanes` defaults to pinned
vLLM's `max_concurrent_batches` and must be at least that host-overlap depth. A
smaller value fails during initialization. Normal execution polls without
blocking; only actual pool exhaustion waits for the oldest submitted lane's
real event, then retires and reuses that lane. A query/wait failure keeps
ownership and metadata. No polling spin, sleep, overwrite, or global stream
synchronization is used. The setting controls ownership cost and pressure
frequency, not Window semantics.

Host tests dependency-inject fake events and prove reverse completion,
pressure, abort and reuse without sleeps. This is not proof of actual NPU stream
ordering. `allow_same_mapping_epoch` is a HOST CONTRACT ONLY and has no current
production caller.

Eagle3 multi-step async and DSA async are not silently enabled: they need,
respectively, a proposal/step live binding and lane-owned backend-derived state.

## 10. Red-to-green evidence

- async metadata lifetime tests failed on the P8 parent because handles lacked
  `bound_metadata`; production now holds it until completion;
- uncompressed DSA/DSA-CP source tests failed because inventory lacked separate
  geometry/compression facts; production now records and validates them;
- DSA-CP shared metadata construction failed with missing
  `common_ratio_to_sas_metadata`; the real builder is now included in the shared
  DSA metadata branch;
- mixed/terminal tests changed the old bypass/reject expectations and now prove
  row-phase identity, full continuing rows and Windowed decode rows.

## 11. Tests and limitations

The authoritative command/result ledger is `P7X_Test_Results.md`. Key results:

- P7-X/P1-P4/attn-utils targeted: 301 passed;
- full spec_decode: 618 passed, 13 skipped, 7 host VWN failures;
- attention: 472 passed, 3 skipped;
- 310P: 155 passed, 2 skipped;
- worker/v2 + block/attn/topology: 147 passed;
- prefix/cache/GLM model tests: 74 passed, 1 skipped;
- distributed: 571 passed in sandbox plus the one socket test passed outside it.

Ruff, format, targeted mypy, compileall, diff-check and locally executable
Python repository hooks passed. Full pre-commit could not install actionlint in
the local environment; gitleaks was unavailable because neither `gitleaks` nor
`wget` exists. These are recorded as environment-blocked, not PASS.

## 12. Final invariants

- vLLM and MRV1 unchanged;
- CONFIG_OFF/FORCED_OFF create zero P7-X state;
- Graph provider/capture untouched; Graph Gate frozen;
- canonical FullSource read-only;
- Target metadata/read full and isolated;
- positions/query/slot/write unchanged;
- no hidden global, ContextVar, owner swap, model-name backend guess, or silent
  full-Draft fallback;
- every admitted identity includes method, backend/group geometry, topology,
  lane, generation, mapping epoch, request ordering and row phases.

## 13. Shared MRV2 DSA-CP metadata fix

`worker/v2/attn_utils.py` recognizes `AscendDSACPMetadataBuilder` as a consumer
of shared DSA request metadata. This correct builder contract is not Window-only
behavior. Window OFF is mandatory regression scope; the explicit CONFIG_OFF unit
test and Node101 `DSACP-00` case guard it.

Window topology validates the raw DSA-CP request, then uses
`vllm_ascend.utils.enable_dsa_cp()` as the effective backend authority. A raw
true/effective false route does not claim DSA-CP or implied FlashComm.

## 14. Independent review and Report1 reconciliation

DeepSeek's two Major, ten Minor, and three Question items were independently
reproduced. Fourteen were accepted and fixed in code/tests/docs; Q-02 was
rejected because topology identity is not proposal/window identity and no stale
W/K alias was found. See `P7X_Review_Resolution.md`.

Report1 ran P8 SHA `4753742...`, not P7-X. Every second-round case must export
`VLLM_USE_V2_MODEL_RUNNER=1` and prove the model-runner plus speculator classes
from inside the worker; otherwise it is `INVALID_RUN_WRONG_MODEL_RUNNER`.

## 15. Next step

Publish the frozen P7-X final SHA, then run the exact second-round Node101
matrix. Do not inherit P8 NPU results, run performance first, or reopen Graph.
