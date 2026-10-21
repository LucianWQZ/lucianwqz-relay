# P7-X MRV2 Draft Sliding Window — Performance Investigation

## 0. Investigation status

- Baseline branch: `feature/p7x-nongraph-completion`
- Baseline SHA: `c1c2129aa49ee1de381130729de73124a6ec893a`
- Baseline tree: `384af8a0466f6aea2e73d6217f9802415b5ccd40`
- Investigation branch: `perf/p7x-draft-window-hotpath`
- vLLM: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`, tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`, clean and unmodified
- Stage at time of this report: read-only architecture review; no production source change had been made
- Decision gate: `OBJECTIVE_AVOIDABLE_OVERHEAD` **found**; targeted optimization is justified
- Graph track: frozen and outside this investigation

Line references below are to the exact baseline SHA above. They are evidence anchors, not durable API locations.

## 1. Runtime evidence

Node101 is `node-39-101`, 16 × Ascend 910 A3. The measured route is true MRV2:

- target: GLM-5.2-W4A8;
- drafter: eligible DSpark, K=8, `sample_from_anchor=true`;
- TP16, DP1, EP on, async on, Draft eager;
- `max_num_seqs=16`, `max_model_len=132096`;
- P7-X SHA `c1c2129...`;
- all 16 ranks reported `NPUModelRunner`, `AscendDSparkSpeculator`, and `VLLM_USE_V2_MODEL_RUNNER=1`.

With output length 2000, four requests, concurrency one, and request rate zero:

| Input | Window | acceptance | output throughput | TPOT | TTFT | E2E |
|---|---:|---:|---:|---:|---:|---:|
| 16K | OFF | 6.1657 | 69.967 tok/s | 11.6 ms | 5422.8 ms | 114.34 s |
| 16K | 1024 | 6.34 | 69.3836 tok/s | 11.7 ms | 5513.3 ms | 115.30 s |
| 128K | OFF | 1.9227 | 16.3255 tok/s | 36.0 ms | 50594.5 ms | 490.03 s |
| 128K | 1024 | 6.0519 | 26.8696 tok/s | 12.2 ms | 50126.4 ms | 297.73 s |

The 16K W1024 result is `-0.83%` throughput versus the current OFF sample and may still be noise. The 128K result proves that the Window read reduction is effective and delivers a large workload-dependent benefit; it does not prove that every Window-only host/device operation is optimal.

## 2. Historical comparison

Historical MRV1 on the same broad GLM/DSpark topology reported:

| Input | MRV1 OFF | MRV1 W1024 | W gain |
|---|---:|---:|---:|
| 16K | 63.2 tok/s | 69.6 tok/s | +10.2% |
| 128K | 15.3 tok/s | 26.8 tok/s | +75.8% |

The important cross-generation observation is:

- MRV2 16K OFF is about 10.7% faster than historical MRV1 OFF;
- MRV2 16K W1024 is within about 0.3% of historical MRV1 W1024;
- MRV2 W1024 absolute TPOT is likewise nearly identical to historical W1024.

Therefore, “MRV2 Window regressed by 10%” is **not supported**. A narrower hypothesis is plausible: constant Window-only control-plane and copy overhead can consume the marginal benefit at 16K while being amortized by the much larger attention saving at 128K. Only a larger NPU A/B/A campaign can quantify that attribution.

## 3. OFF versus Window call graph

### OFF

```text
AscendDSparkSpeculator.propose
  -> DraftWindowEagerMixin._draft_window_proposal_scope
       epoch source absent -> immediate yield
  -> upstream DSpark/DFlash prepare_dflash_inputs (once)
  -> upstream _build_draft_attn_metadata
       full block table views
       full device seq_lens
       CPU upper allocation/update
  -> Ascend metadata builder
  -> DSpark draft forward + sequential Markov head
```

CONFIG_OFF and FORCED_OFF never initialize P2/P3/P7 state, so OFF does not allocate workspace, async lanes, descriptors, or Window metadata.

### W1024

```text
AscendDSparkSpeculator.propose
  -> proposal scope / phase classification / generation epoch
  -> async lane acquire
  -> upstream prepare_dflash_inputs (once, full positions and full slot mapping)
  -> DraftWindowEagerMixin._build_draft_attn_metadata (once)
       exact device seq_lens -> CPU snapshot
       CPU upper calculation
       CPU resident valid-count gather
       row-wise Window plan/descriptors
       workspace materialization from canonical FullSource
       typed input validation
       Draft-private Ascend metadata build
       Target alias isolation/validation
       async bind
  -> same DSpark draft forward + sequential Markov head
  -> event record / submit / deferred retirement
```

For DSpark K=8 with `sample_from_anchor=true`, `num_query_per_req=K`. The complete parallel draft is one forward and the Window path is materialized **once per outer proposal**, not eight times. The Markov head still loops over K, but that loop exists in OFF and ON and is not Window overhead.

## 4. Window-only per-step work

| Operation | OFF | W1024 | Frequency | Device operation | Allocation/sync |
|---|---|---|---|---|---|
| policy/capability inventory | factory baseline | evaluated when capability is initialized | init only | no | immutable objects/workspace init |
| phase classification | none | row classifier plus freshness rechecks | several host checks per proposal | no | tuples/dataclass/small arrays |
| generation/identity | none | epoch, request/mapping/phase identity | once per proposal | no | small Python objects |
| exact length snapshot | none in upstream DSpark metadata seam | draft device seq_lens copied to CPU | once per proposal | D2H | synchronizing exact-length dependency |
| CPU upper | upstream full upper | Window apply-time full upper | once per proposal | no | one CPU tensor |
| resident counts | none | canonical CPU valid-count gather | once per proposal | no | tensor + index conversion; baseline contains a redundant clone |
| Window planning | none | S/E/V and descriptor per active row | once per proposal | no | two CPU tensors + descriptors |
| workspace pre-clear | none | all table/count/length buffers zeroed | once per materialization | NPU + CPU | full-capacity clears |
| table materialization | full table view | required canonical row slice copied into stable Window table | once per row/proposal | NPU D2D | required columns only |
| length materialization | full seq_lens view | valid counts and exact copied H2D; CPU exact/upper copied | once per proposal | H2D + CPU | stable backing |
| Draft metadata | baseline builder | vendor-local equivalent with explicit Window read inputs | once per proposal | backend-dependent | metadata objects |
| isolation | none | clone aliases, then independent store validation | once per proposal | clone only on alias | recursive host walk |
| async acquire | baseline scheduler | bounded Window lane | once per proposal | event query of submitted lanes | unconditional reclaim scan before baseline optimization |
| completion | none for Window backing | new completion event, record, submit | once per proposal | NPU event | correctness-required lifetime token |
| workspace retirement clear | none | all buffers zeroed after reader completes | once per proposal/lane reuse | NPU + CPU | full-capacity clears |

## 5. Allocation audit

### Proven Window-only allocations

1. `draft_window_eager.py:411-415` allocates `cpu_apply_time_full_upper` each proposal.
2. `draft_window.py:1295-1302` allocates a CPU valid-count tensor and may allocate an int64 mapping conversion.
3. `draft_window_nongraph.py:215-221` immediately clones the newly allocated valid-count tensor. This clone has no independent owner/lifetime purpose: `gather_valid_num_blocks_cpu` already returns a new caller-owned tensor. This is objectively redundant.
4. `draft_window_nongraph.py:253-254` allocates exact and upper CPU tensors each proposal.
5. Dataclass/tuple/list objects are built for phase plan, resident snapshot, descriptors, generation, transport, and metadata store entries.
6. `DraftWindowNPUEventCompletionToken.record_current_stream` creates one NPU event per successful async proposal. Reuse could be possible in principle, but event-reset semantics and real stream evidence are not established locally; changing it is not justified in this round.

The small CPU tensors are real but unlikely by themselves to explain the observed NPU result. The redundant clone is safe to remove; broader scratch-buffer pooling would complicate async ownership for little demonstrated benefit.

## 6. Host-device synchronization audit

### Proven Window-only synchronization

`draft_window_eager.py:386-395` copies prepared Draft `seq_lens` from device to CPU once per proposal. This is a true D2H exact-length dependency. The CPU exact lengths are used to derive S/E/V and are then consumed by FIA metadata (`seq_lens_list`), so removing or replacing them with an optimistic upper would change the frozen correctness contract.

The model runner also schedules a D2H copy of corrected request state after target postprocessing. Source review shows that state is not exposed to the speculator as an exact, generation-bound carrier. Reusing it would require a new explicit ownership/timing seam and NPU ordering evidence; it is a future P0 candidate, not a safe local edit here.

The following `.item()` calls are on CPU tensors and do not trigger NPU D2H:

- row exact/upper/valid extraction in the host planner;
- CPU upper maximum in the read-input adapter;
- descriptor validation when a CPU valid-count snapshot was supplied.

Async `event.query()` is nonblocking by contract; `event.synchronize()` occurs only under bounded-pool pressure. The baseline implementation nevertheless queried submitted lanes before every acquisition even if another lane was already free. Those queries are unnecessary for correctness in the no-pressure case.

## 7. Python-loop audit

- Phase classification loops over active rows.
- Materialization planning loops over active rows.
- Workspace table copying loops over active rows.
- Metadata isolation recursively walks Draft and Target metadata.
- Async reclamation loops over bounded lanes.
- DSpark's K-step Markov sampling loop is shared by OFF and ON.

For the measured batch size one, row loops are not a leading suspect. Vectorizing them would add complexity without removing the D2H or device kernels. The async lane scan is bounded, but its event queries can be deferred until pressure.

## 8. Block-table audit

The canonical FullSource remains a borrowed full table. Window materialization copies only each descriptor's required columns into a stable-address, speculator-owned workspace; slot mapping still comes from the canonical full `BlockTables` owner.

P7-X enlarged each workspace table to the canonical source row width to support continuing-prefill rows in mixed batches. Consequently, `DraftWindowWorkspace._zero_all` clears the **full source-width backing**, even when a pure-decode W1024 descriptor uses only a small prefix of that workspace. It runs:

1. at the start of every materialization (`draft_window.py:1739`, baseline anchor); and
2. again when the prior generation retires through `reset` (`draft_window.py:1829-1845`).

Thus the successful steady-state path performs two full-capacity clear sequences per generation in addition to the required narrow row copy. The backing is already zero after construction or retirement, so the pre-materialization clear is redundant. An active-footprint retirement clear was also investigated, but the non-contiguous prefix clear regressed the local proxy benchmark; the accepted low-risk change therefore keeps the original contiguous full reset at retirement and removes only the proven duplicate pre-clear. Rare exception recovery also retains a full clear.

Skipping table refresh merely because S is unchanged is **not safe** in the current contract. There is no canonical block-table content version, and prefix residency, row replacement, or block recycling may change source contents without changing S or the Tensor address. The canonical slice copy remains required.

## 9. Length-state audit

- Full exact: authoritative prepared Draft device `seq_lens`; one Window-only D2H snapshot.
- Full upper: `InputBatch.seq_lens_cpu_upper_bound + actual query width`, clamped.
- Window exact/upper: independently allocated CPU vectors, then copied into lane-owned stable backing.
- Device Window exact: copied once to the active lane and consumed by metadata/operator.
- `max_seq_len`: computed from CPU upper; no device sync.

There is no repeated upper-bound recomputation within one DSpark proposal. Exact and upper cannot be merged because they have different semantics and consumers.

## 10. Async audit

The measured route has async scheduling enabled. Per proposal:

- `acquire_with_backpressure` calls `reclaim_completed` first;
- `reclaim_completed` queries every submitted lane;
- a free lane may already exist, making those queries unnecessary;
- on actual pressure, waiting only for the oldest submitted event is correctness-required and remains unchanged;
- a completion event is recorded after Draft forward, and backing remains owned until completion.

Safe optimization: first attempt acquisition without polling. Only when no free lane exists, reclaim completed lanes, retry, then wait for the oldest event if pressure remains. This preserves bounded ownership and reverse-completion behavior while removing no-pressure event queries.

## 11. Capability/gate audit

Policy, method normalization, backend inventory, provider selection, topology, graph, parallel, and hardware-family checks execute during source-capability initialization in `set_attn`, not once per decode step. The hot path uses the prebound capability/provider/runtime objects. No repeated full capability dispatch was found in the measured path.

Freshness validation is intentionally repeated around the D2H and host plan. It detects request reorder, row replacement, mapping rewrite, and phase mutation. It must not be removed merely for performance. One phase classification is duplicated before epoch creation to preserve the zero-epoch pure-prefill bypass; reducing it would require a carefully typed preflight result. Its cost is small and no change is proposed in this round.

No hot-loop logger calls were found in the Window modules or DSpark integration path.

## 12. MRV2 OFF efficiency assessment

Source comparison does not identify a Window path that disables DSpark's MRV2 parallel backbone, Markov sampler, local-argmax behavior, EP communication, or target/draft prepare kernels. OFF and ON share those mechanisms. Window ON intercepts only Draft read metadata and adds the control/copy/lifetime work listed above.

Classification:

- **PROVEN:** Window ON adds a constant D2H exact-length dependency, stable workspace copies/clears, metadata isolation, and async event lifecycle.
- **PROVEN:** the baseline performs redundant full workspace clearing and no-pressure event polling.
- **LIKELY:** constant Window-only overhead is more visible at 16K and amortized at 128K.
- **POSSIBLE:** the D2H exact snapshot is the dominant constant cost; only NPU profiler evidence can rank it.
- **NOT SUPPORTED:** Window ON bypasses or disables a known MRV2 model-forward efficiency mechanism.
- **NOT SUPPORTED:** the four-request `-0.83%` sample proves a deterministic performance regression.

## 13. Ranked suspects and decisions

| Rank | File/function | Frequency | Why it costs | Safe optimization | Risk / decision |
|---|---|---:|---|---|---|
| P0 | `draft_window.py`, `DraftWindowWorkspace.materialize/reset/_zero_all` | two full clears per successful generation | multiple device ops; P7-X table capacity is full source width | remove redundant pre-clear; retain the established contiguous retirement reset | low with padding/tail/exception regression tests; **implement** |
| P0 | `draft_window_eager.py`, `_snapshot_prepared_draft_seq_lens` | one D2H per proposal | host waits for exact device state | future generation-bound reuse of already scheduled runner D2H | high without a typed ownership/timing seam; **do not change** |
| P1 | `draft_window_async.py`, `acquire_with_backpressure` | lane scan/query every proposal | event queries occur even when a lane is free | acquire first; poll only on pressure | low; **implement** |
| P1 | `draft_window_nongraph.py`, `build_prefix_resident_snapshot` | one CPU clone per proposal | duplicates an already newly allocated tensor | remove `.clone()` | very low; **implement** |
| P2 | proposal phase/freshness checks | multiple host passes | tuple/dataclass/NumPy bookkeeping | typed preflight reuse | correctness-sensitive and small; **defer** |
| P2 | metadata isolation | recursive host walks | defensive nested alias proof | proof token / builder-specific non-alias contract | correctness-sensitive; **defer** |
| rejected | block-boundary-only table refresh | potentially every non-boundary proposal | could avoid D2D row copy | cache by S/descriptor | unsafe without canonical content version; **reject** |

## 14. Optimization decision

```text
OBJECTIVE_AVOIDABLE_OVERHEAD: YES
```

The production edit is constrained to three behavior-preserving changes:

1. eliminate the redundant full-capacity pre-materialization clear while retaining the established full retirement and exception cleanup;
2. avoid querying submitted async lanes while a free lane is immediately available;
3. remove the redundant CPU valid-count clone.

No policy, S/E/V math, block-table source, slot mapping, position, KV-write, Target, method, graph, topology, or async completion semantics may change.

### Post-investigation implementation refinement

The read-only review initially proposed narrowing retirement cleanup to the active table footprint. A red-to-green prototype preserved correctness, but a same-host microbenchmark showed the strided prefix clear was slower than the original contiguous reset. That sub-change was rejected before commit. The delivered workspace optimization is intentionally narrower: one successful generation now performs one full cleanup at retirement instead of one pre-clear plus one retirement clear. This note records the evidence-driven refinement rather than rewriting the original investigation history.

## 15. Required verification before accepting the optimization

- red-to-green tests for workspace clear footprint and no duplicate pre-clear;
- async tests proving zero query with a free lane and unchanged pressure/reverse-completion behavior;
- ownership test proving the resident snapshot remains independent without the clone;
- P7-X targeted suite and affected P1–P7 regressions;
- Ruff, format, targeted Mypy, compileall, and diff-check;
- local CPU microbench with warmup/multiple rounds/median, explicitly classified as host bookkeeping evidence only;
- Node101 A/B/A revalidation for 16K and 128K before any NPU performance claim.
