# P7-X Graph Patch NPU Handoff

## Purpose and hard boundary

This handoff describes the future company-NPU campaign for local spike
`c43989aabd9b40a561987d39f4ba4516934f2f5b`. No NPU experiment was run during
the source spike. The Graph Window product Gate remains closed.

Initial characterization scope:

- DFlash and eligible non-V4 co-trained DSpark only;
- single executable group;
- dense GQA/FIA direct-prefix backend;
- TP=DP=PP=PCP=DCP=1;
- no SP, DSA-CP, FlashComm, async, or prefix cache;
- exact pinned vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c`;
- exact local Ascend spike SHA above.

Eagle3, complex backends, TP16, and product enablement are excluded.

## Required artifact identity

Every run must record:

- host and NPU model/family;
- driver, CANN, PyTorch, torch-npu versions;
- vLLM SHA/tree and clean status;
- vLLM-Ascend SHA/tree and clean status;
- complete expanded command/config;
- target and draft model resolved paths/revisions;
- method, W, K/query width, graph mode, topology;
- seed and request fixture;
- raw logs, trace, profiler files, and checksums.

Do not reuse earlier eager or P7-X evidence as Graph evidence.

## G1 — Startup capture operand identity

Goal: prove the actual captured Draft FIA operand uses the P6 persistent carrier
addresses.

Required evidence:

1. Before capture, record `DraftWindowGraphCaptureIdentity` and tensor address,
   shape, dtype, device for table/device exact/CPU exact/upper.
2. At the real backend/task capture boundary, record the operand addresses
   actually registered by ACL Graph.
3. Prove exact address equality for the Window read carriers.
4. Prove slot mapping points to canonical full persistent storage.
5. Prove no Target metadata/storage alias.

Pass: captured operands exactly match the registered P6 backing and all
write-side invariants hold. A Python builder-call trace alone is insufficient.

## G2 — Runtime persistent-content refresh

Goal: prove replay sees new content at unchanged addresses.

Use A/B/A':

```text
A  = generation g, mapping_epoch e, request fingerprint r1
B  = generation g+1, mapping_epoch e+1, different mapping/content
A' = semantic content like A, new generation and epoch
```

Required evidence:

- table and lengths addresses remain stable;
- table and length content fingerprints differ A→B and restore semantically
  for A';
- stale A identity cannot authorize A';
- B does not contaminate A';
- canonical FullSource and Target/write state stay unchanged.

## G3 — Actual physical read proof

Goal: prove the Draft attention operator reads exactly the intended Window
physical set.

Cases:

- short context;
- exact block boundary;
- non-boundary;
- long context;
- W and W+B-1 capacity edge;
- DFlash K+1 width;
- DSpark K and explicit K+1 widths;
- reorder and finish/add if constructible within the initial topology.

For every case record CPU oracle S/E/V, full source columns, materialized table,
valid counts, exact/upper lengths, and the backend/operator physical read set.

Pass: physical blocks/tokens match the independent oracle; no window-of-window
source is observed.

## G4 — Full slot/write invariants

Goal: prove read-window injection does not change write-side semantics.

Compare Window OFF/ON under controlled identical state:

- slot mapping values and storage owner;
- positions and query-start layout;
- physical KV allocation/write locations;
- canonical full table;
- Target metadata and Target logits where observable;
- final accepted output under a controlled seed.

Pass: only Draft read table/length visibility differs.

## G5 — Replay/update timeline

Goal: resolve `NEEDS_NPU_TIMELINE`.

Trace, for each generation:

```text
materialize/bind
-> replay submission
-> operator consumer
-> update_full_graph_params source
-> backend task update
-> effective replay generation
-> completion/retire
```

Explicitly determine whether `UPDATE(N)` affects replay N, N+1, or a distinct
task launch. Include a one-step-lag oracle that would fail if table and length
belong to different generations.

Pass: effective-generation mapping is unambiguous and no early overwrite is
possible. Do not infer this from Python call order alone.

## G6 — Topology expansion

Only after G1–G5 pass at topology 1 may the owner open separate expansions:

1. TP>1, ultimately TP16 if required;
2. DP/PP/PCP/DCP;
3. SP/DSA-CP/FlashComm;
4. prefix and async;
5. complex backends.

Each requires a new route fingerprint, rank-local read projection, physical
read oracle, lifecycle proof, and negative mismatch tests. Do not remove P6
guards merely because the startup seam works at TP1.

## G7 — Performance

Compare Draft Graph Window OFF/ON and Draft eager Window ON with identical
model/config/request fixtures. Record:

- capture time and memory;
- warmup and repetition count;
- metadata/materialization cost;
- D2H/H2D and synchronization;
- replay/update/event overhead;
- HBM and CPU memory;
- TTFT, TPOT, throughput, acceptance rate, end-to-end latency;
- raw profiler timeline and contention/noise rejection criteria.

Use A/B/A ordering and deterministic seeds. Functional correctness gates G1–G5
must close before interpreting performance.

## Negative campaign

Confirm hard rejection or zero-state behavior for:

- CONFIG_OFF and forced-OFF methods;
- Eagle3 and DFlash2;
- DSA, DSA-CP, SFA, MLA, recycling/native;
- multi-group;
- topology outside P6 fingerprint;
- async and prefix;
- stale descriptor, bucket, backing, generation, mapping epoch, route, gid,
  lane, phase, and step;
- Target or canonical-owner alias.

An environment/configuration failure is not an expected Gate result.

## Stop conditions

Stop and keep Graph frozen on any of:

- captured address differs from P6 backing;
- Window table or length lags by one generation;
- slot/write/Target changes;
- operator physical read exceeds the oracle;
- early carrier overwrite;
- unresolved replay/update effective generation;
- fallback to Target/full metadata while Window provider is present.

## Required campaign verdict

Report each phase independently:

```text
G1 CAPTURE ADDRESS: PASS / FAIL / BLOCKED
G2 PERSISTENT REFRESH: PASS / FAIL / BLOCKED
G3 PHYSICAL READ: PASS / FAIL / BLOCKED
G4 FULL WRITE INVARIANTS: PASS / FAIL / BLOCKED
G5 TIMELINE: PASS / FAIL / BLOCKED
G6 TOPOLOGY: NOT STARTED / scoped result
G7 PERFORMANCE: NOT STARTED / scoped result
GRAPH WINDOW SUPPORT: STILL FROZEN unless separately authorized
```

