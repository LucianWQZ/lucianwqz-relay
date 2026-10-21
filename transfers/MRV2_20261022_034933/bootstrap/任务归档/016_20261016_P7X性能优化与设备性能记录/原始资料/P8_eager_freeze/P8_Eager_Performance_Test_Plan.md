# MRV2 Draft Sliding Window — P8-E Performance Test Plan

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

No performance result is generated locally. This plan defines how a future NPU
campaign must measure cost and benefit without hiding synchronization or contention.

## 1. Test principle

For each owner-mandatory positive route, compare:

```text
A  = Window OFF, exact model/config/request fixture
B  = Window ON, only draft_window_size differs
A' = Window OFF repeated after B
```

Reject the comparison if the model revision, topology, sampling, cache config,
compiler mode, request tokens, process placement, thermal/power state, device load,
or effective backend differs. Graph stays NONE and async stays false.

## 2. Environment record

Archive machine/device/firmware/driver/CANN/container, CPU/NUMA affinity, NPU
frequency/power mode, vLLM/vLLM-Ascend SHAs and trees, model realpaths/revisions,
expanded argv/environment, topology fingerprint, dataset hash and all profiler
versions. Record other device processes before and after each run.

## 3. Workloads

For Eagle3, DFlash and eligible DSpark separately:

- short context (`H<=W`);
- near exact block boundary;
- non-boundary;
- long context substantially larger than W;
- output lengths 1, 32, 128 and owner production percentile;
- single request and, only after G-MIXED closes, controlled concurrency;
- Eagle3 K=3 future-column and rejection cases;
- DSpark K and K+1 modes;
- DFlash K+1 mode.

Correctness campaign must pass before its performance sample is admissible.

## 4. Warmup and repetition

1. Start a fresh service for each A/B/A' sequence or prove cache/state reset.
2. Perform at least 10 unmeasured warmup requests and continue until the last five
   latency samples vary by less than an owner-set threshold.
3. Collect at least 50 measured repetitions per short case and 30 per long case;
   use more if the bootstrap confidence interval remains wide.
4. Randomize A/B/A' block order across at least three independent service starts.
5. Reject runs with unrelated device contention, throttling, OOM recovery, graph
   fallback, request failure, or a topology fingerprint change.
6. Keep raw per-request samples; do not report only averages.

## 5. Component ledger

Instrument timestamps/counters around the exact owners without adding blocking
copies to production timing:

| Component | Measurement boundary | Required metric |
|---|---|---|
| policy/capability | policy entry → `require_live_materialization` | CPU µs, allocations |
| planner | L0/E input → scalar plan/descriptors | CPU µs |
| valid-count gather | source bind → gathered counts ready | CPU and device µs, bytes |
| table materialization | workspace write begin/end | device µs, H2D bytes, rows/columns |
| metadata build | validated inputs → Draft store publish | CPU/device µs, allocations |
| Draft forward | operator submit → measured completion | kernel/device µs |
| acceptance/rejection | Draft output → accepted tokens | CPU/device µs |
| D2H | every feature-attributable transfer | count, bytes, latency, synchronization cause |
| H2D | every feature-attributable transfer | count, bytes, latency |
| synchronization | stream/event/device synchronizations | count, blocking duration, caller |
| event overhead | record/query/wait when later applicable | count and µs; currently async live is absent |
| CPU memory | process RSS/USS and allocations | peak and delta |
| HBM | allocated/reserved/peak | peak and delta |

P3 debug `.cpu()` validators and host fake completion must not appear in the
production hot path. If tracing itself synchronizes, collect an uninstrumented E2E
run and label the instrumented result separately.

## 6. End-to-end metrics

Report by method, context bucket and output length:

- TTFT;
- TPOT / inter-token latency;
- request latency;
- accepted draft tokens and acceptance rate;
- generated tokens/s per request;
- aggregate throughput requests/s and tokens/s;
- CPU utilization and memory;
- NPU utilization, HBM, kernel time and idle gaps;
- error/retry rate.

Use median, mean, standard deviation, p50, p90, p95 and p99. Report paired B−A
and B/A ratios with 95% bootstrap confidence intervals. A and A' disagreement must
be investigated before attributing B deltas to Window.

## 7. D2H/H2D and synchronization audit

The report must enumerate baseline transfers and feature-attributable net additions
per proposal. For each transfer record source tensor, destination, shape/dtype,
caller, whether it blocks the submitting thread, and why it cannot be derived from
an existing same-source CPU/device value. A count without call-site attribution is
insufficient.

## 8. Memory audit

Separate:

- persistent canonical full state (baseline);
- P3 stable Window workspace;
- metadata/store objects;
- transient builder tensors;
- profiler/debug buffers.

Verify Window workspace capacity is bounded by the documented geometry and does
not grow per proposal. Verify OFF and forced-OFF allocate no Window/P7 state.

## 9. Pass/fail policy

Owner must provide numerical thresholds before a release verdict. Until then:

- complete, uncontended raw artifacts produce `MEASURED`, not `PASS`;
- missing component attribution, synchronization, correctness, or A' stability is
  `INSUFFICIENT_EVIDENCE`;
- any correctness divergence invalidates the performance run;
- async, parallel and Graph performance are out of scope because those live routes
  remain disabled.

## 10. Artifact layout

```text
performance/<method>/<device>/<workload>/<A|B|A-prime>/
  manifest.json
  expanded_argv.txt
  request_fixture.json
  raw_samples.csv
  component_timeline.jsonl
  transfer_ledger.csv
  profiler/
  memory.csv
  service.log
  summary.json
  SHA256SUMS
```

```text
EAGER PERFORMANCE VERIFIED: NO
R4/P8 PERFORMANCE CAMPAIGN: NOT RUN
```
