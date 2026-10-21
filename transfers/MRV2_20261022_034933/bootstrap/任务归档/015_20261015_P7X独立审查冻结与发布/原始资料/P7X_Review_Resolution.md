# P7-X Independent Review Resolution

## Review identity

- Original implementation: `7e88db6ed31e7965f526ea6f49cc17101f4a65b4`
- Original tree: `71800e2e250f0b4dc51aede643eebff55e39b404`
- Review: `P7X_DeepSeek_Independent_Review.md`
- Runtime reconciliation source: Report1 at
  `/Users/wenqingzhang/Desktop/Node101_MRV2_P8_Current_Final_Campaign_Combined_Report.md`
- Report1 SHA256:
  `cfd15811303b30d0786cf4541b2190ac7a66e349ba55e160b6f4dff065408bbf`
- Review-fix commit: `c1c2129aa49ee1de381130729de73124a6ec893a`
- Final tree: `384af8a0466f6aea2e73d6217f9802415b5ccd40`

Evidence order was current source, reproducible source/math, independent
reproduction, Report1 facts, host/static tests, older evidence, documentation,
then inference. Report1 ran P8 SHA `4753742...`, not P7-X, and is not promoted
to P7-X NPU evidence.

## Finding statistics

```text
ACCEPTED=14
PARTIALLY_ACCEPTED=0
REJECTED=1
INSUFFICIENT_EVIDENCE=0
REPORT1_DEPENDENT=0
NPU_DEPENDENT=0
```

The remaining NPU Gates are route evidence requirements, not unresolved
review-finding classifications.

## Resolution table

| Finding | Reproduced | Resolution | Production change | Docs change | Tests | Report1/NPU |
|---|---|---|---|---|---|---|
| M-01 | Yes. `attn_utils.build_attn_metadata` is shared by Window OFF and ON; the DSA-CP builder needs common DSA kwargs. Parent-red reproduced the missing-key failure. | `ACCEPTED` | No revert: the shared fix is correct. | Identify it explicitly as a shared MRV2 DSA-CP metadata fix. | Added an explicit CONFIG_OFF DSA-CP shared-builder regression. | Added `R1-DSACP-OFF-01` and `DSACP-00`; NPU still required. |
| M-02 | Yes. DFlash/DSpark default async is reachable; fixed capacity 2 previously raised mid-proposal when all lanes were owned. | `ACCEPTED` | Capacity defaults to `max_concurrent_batches`, configured capacity below that fails at initialization, and actual exhaustion waits only the oldest submitted lane's real completion event before safe retirement/reuse. | Document key, range, lower-bound rationale, pressure behavior, and NPU limit. | Red first: missing pressure API, live third proposal failure, and absent capacity validation. Green covers capacity 1/2, third proposal, reverse completion, abort-after-submit, query/wait error, retained metadata, prefix and TP identity. | Real event/stream ordering and capacity remain mandatory NPU cases. |
| m-01 | Yes. `P7EagerTopologyFingerprint` did not contain explicit W/K fields. | `ACCEPTED` | None. | Corrected topology spec: W/K are proposal/read identities, not topology fields. | Existing mismatch tests retain the boundary. | None. |
| m-02 | Yes. The old P7 evaluator has no production caller and its matrix had stale canonical wording. | `ACCEPTED` | No risky dead-code cleanup. | Mark old P7 matrix historical/superseded-by-P7X. | Source call-site search recorded. | None. |
| m-03 | Yes. `DraftWindowResidentSetSnapshot.validate_expected` had no production caller. | `ACCEPTED` | Removed the misleading unused method. Runtime freshness remains enforced by generation/mapping/request/source/valid-count data consumed by materialization. | Clarified the actual identity chain. | Snapshot mutation test now asserts source/mapping stability and changed valid counts without invoking a fake production invariant. | None. |
| m-04 | Yes. `draft_window_async_lanes` was undocumented. | `ACCEPTED` | Policy changed with M-02. | Documented type, default, minimum, pressure behavior, and performance effect. | Default and too-small capacity regressions added. | NPU pressure case retained. |
| m-05 | Yes. `allow_same_mapping_epoch` has no production caller. | `ACCEPTED` | None. | Marked HOST CONTRACT ONLY / NOT CURRENT PRODUCTION REACHABILITY. | Host state-machine tests remain. | Any future live use needs a new evidence cycle. |
| m-06 | Yes. Raw `additional_config.enable_dsa_cp` could disagree with the validated backend authority. | `ACCEPTED` | Runtime context now claims DSA-CP only when requested and the same effective `enable_dsa_cp()` authority used by backend selection is true; FlashComm follows effective state. | Documented request versus effective truth. | Red-to-green tests cover raw true/effective false and final replicated provider fingerprint. | Actual DSA-CP remains NPU-required. |
| m-07 | Yes. Valid block count is allocated/current canonical extent, not a universal physical-residency probe. | `ACCEPTED` | None. | Corrected terminology; future offload/SFA/recycling requires a real resident-set provider. | Existing allocation/eviction identity tests retained. | Prefix physical behavior remains NPU-required. |
| m-08 | Yes. TP x async combination lacked a register row. | `ACCEPTED` | None. | Added `R1-TP-ASYNC-01`. | Prefix+TP pressure identity host test included. | New per-rank stream/event case required. |
| m-09 | Yes. Prefix x async lacked a register row. | `ACCEPTED` | None. | Added `R1-PFX-ASYNC-01`. | Prefix+pressure host identity test included. | Shared block lifetime/eviction/reuse requires NPU. |
| m-10 | Yes. Ordinary TP x DSA/DSA-CP lacked a register row. | `ACCEPTED` | None. | Added `R1-TP-DSA-01`. | Source topology/provider tests retained. | Rank-local derived state and communication require NPU. |
| Q-01 | The product rule in the adjudication request makes Window-OFF baseline regression mandatory. | `ACCEPTED` | None beyond the already-correct shared builder fix. | Recorded as `RESOLVED: MANDATORY REGRESSION`. | Explicit CONFIG_OFF DSA-CP test added. | `DSACP-00` is mandatory. |
| Q-02 | No stale-alias counterexample was found. Topology fingerprint identifies topology; W/K are bound by WindowPlan, provider expected future offset, read descriptors, and generation identity. | `REJECTED` | No duplicate W/K topology fields added. | Corrected the overclaim and documented the ownership split. | Provider mismatch and generation/descriptor tests cover the actual boundary. | Artifact collection still records W/K explicitly. |
| Q-03 | The previous fixed-capacity crash was not an acceptable steady-state policy. | `ACCEPTED` | Resolved with early lower-bound validation plus pressure-only wait of the oldest real completion event; no overwrite, polling spin, sleep, or global stream sync. | Frozen as the local product safety result. | Same M-02 red-to-green suite. | NPU must prove stream ordering, event visibility, and throughput. |

## Async safety conclusion

Pinned vLLM defines `max_concurrent_batches` as host overlap depth (PP fill and
async overlap). It is used as a minimum/default capacity, not claimed to be the
device lane count. Each configured lane still owns an independent P3 runtime
and stable workspace. Normal proposals only nonblocking-poll completed lanes.
Only actual exhaustion synchronizes the oldest submitted lane's event. A wait
or query failure preserves ownership and metadata; no in-flight backing is
overwritten.

This closes the host/static pressure bug. It does not prove NPU event ordering,
communication-stream completion, or acceptable performance.

## Final route decisions

- TP16: `LOCAL_STATIC_READY`, per-rank NPU evidence open.
- DSA-CP: `LOCAL_STATIC_READY`, including mandatory Window-OFF regression;
  actual local metadata/comm/operator evidence open.
- Async DFlash/eligible DSpark: `LOCAL_STATIC_READY`; NPU event/stream/lifetime
  evidence open. Eagle3 and DSA/DSA-CP async remain runtime-dependent.
- Prefix, chunked, mixed, and multi-request: `LOCAL_STATIC_READY`; new-SHA NPU
  evidence open.
- GLM required route: `REPORT1_RUNTIME_DEPENDENT` until an MRV2 P7-X run reports
  the actual Draft backend, builder, gids, and geometry.
- Graph remains frozen; vLLM and MRV1 remain unchanged.

