# MRV2 Draft Sliding Window — P8-E Remaining Runtime Gate Ledger

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

| Gate | Current state | Exact closing experiment | Required artifact | Release impact |
|---|---|---|---|---|
| `G-GQA-EAGER` | OPEN | P7-final DFlash and eligible DSpark OFF/ON A/B/A on each mandatory device; include K/K+1 routes, physical operand/read oracle, full slot/Target equality, lifetime and profiler | Commands/config, model identities, semantic/table/operator traces, profiler, SHA256 index | Blocks claiming P4a runtime support |
| DFlash/DSpark campaign identity | `OWNER_BLOCKED` input | Owner signs immutable target/draft pairs and supplies absolute realpaths, revisions/config hashes and device assignment; DSpark K+1 pair resolves draft HF `sample_from_anchor=false` | Signed owner matrix plus archived model manifests | Blocks executing DFA/DSP cases, but does not invalidate their static `READY_FOR_NPU` route classification |
| `G-AR-STEP` single request rerun | OPEN at P7 SHA | Repeat Eagle3 K=3/W=64 campaign at `4753742...` on each mandatory device | Full L3/L4/L5-or-explicit-gap record, Target/write and lifetime artifacts | Old P4 evidence cannot certify P7 final |
| `G-AR-STEP` multi-request | OPEN | Construct controlled batch>1 pure decode without scheduler hack; verify rows, reorder, finish/add, mapping epoch and isolation | Scheduler trace, per-row oracle, outputs, operator/event trace | Blocks general serving claim |
| `G-MIXED` | `OWNER_BLOCKED`, `RELEASE_BLOCKER` | Owner chooses (A) implement safe mixed support or (B) approve single-active scope and early admission rejection; then test no EngineCore-wide abort | Written owner decision, production design/commit if needed, fault-containment tests | Blocks Eager release |
| Independent slot oracle | OPEN | Recompute full physical write slots from canonical table + absolute position and compare OFF/ON complete rows | Untruncated tables, positions, computed slots and operator/write trace | Blocks strong write-side runtime claim |
| Physical Draft read | OPEN at L5 | Kernel/profiler trace or approved backend oracle proves actual read interval/table, not only metadata arguments | Raw profiler/kernel evidence linked to proposal identity | Blocks full physical-read claim |
| Device lifetime | OPEN | Record real event at consumer completion; A/B/A overwrite pressure proves no early reuse | Stream/event timeline, addresses, generation ids, raw trace | Blocks async/lifetime claim; important even for serialized proof |
| True row reuse | OPEN | Observe persistent row R owned by request A, retire, then different request D reuses R; stale A is rejected | idx_mapping/request/epoch trace and outputs | Blocks row-reuse acceptance |
| Hardware A2 | old scoped evidence only | Rerun exact P7 candidates on selected A2 model pairs | Device/firmware/container manifest plus full campaign | Device-specific support decision |
| Hardware A3 | UNKNOWN | Execute full positive and negative campaign on an A3 machine | Same artifacts as A2; no inherited result | Blocks A3 support |
| Hardware A5 | UNKNOWN | Execute full positive and negative campaign on an A5 machine | Same artifacts as A2; no inherited result | Blocks A5 support |
| P7 complex backend | FAIL_CLOSED | Not a current positive campaign; requires return to P7 with typed backend provider before NPU | New reviewed implementation + static/NPU evidence | No release impact if documented unsupported; blocks adding those routes |
| P7 parallel | FAIL_CLOSED | Return to P7 for rank-local carrier; then per-topology NPU campaign | New implementation, topology trace, rank-local read/write oracle | No impact on TP1 release scope if owner excludes; otherwise blocker |
| P7 async | STATIC_READY / live fail closed | Return to P7 for live binding and real completion event, then 2+ inflight/reverse completion/abort campaign | Event trace, pool/lane artifacts, profiler | Blocks async support; not ready for NPU today |
| Prefix cache | FAIL_CLOSED | Return to P7 for explicit isolation/provider contract, then NPU A/B | Cache identity, read/write/eviction traces | Blocks prefix-enabled scope |
| Performance | NOT RUN | Controlled OFF/ON A/B/A with warmup, repetition, contention rejection and component timings | Raw profiler, latency/throughput/memory samples and statistics | Blocks release performance acceptance |
| Owner mandatory matrix | PARTIAL | Owner signs exact positive/negative scope, devices, serving mode and evidence thresholds | Reviewed matrix revision | Blocks release acceptance |
| Graph requirement | FROZEN | Not a P8-E experiment; owner must reopen track after a legal capture seam or boundary change | Separate Graph design, review, capture/NPU campaign | Blocks full-feature release, not local Eager campaign entry |

## Gate discipline

An environment/setup failure is not an expected Gate result. A negative test passes
only when the configured route reaches the intended policy/capability reason before
FullSource/workspace creation and leaves baseline state intact.

```text
READY FOR COMPREHENSIVE EAGER NPU: YES
EAGER RELEASE: HOLD
FULL FEATURE RELEASE: HOLD
```
