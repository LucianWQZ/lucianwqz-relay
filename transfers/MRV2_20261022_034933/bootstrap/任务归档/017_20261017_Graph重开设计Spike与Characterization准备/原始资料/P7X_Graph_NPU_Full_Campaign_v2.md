# P7-X Graph NPU Full Campaign v2

## Purpose and Safety Boundary

This plan is for a future company-server session. It does not assert Graph support. The internal candidate is default-off and must only run on the exact characterization branch/commit. The public Graph Window user gate remains fail closed.

```text
Candidate commit: 8cb4bed670f395c257c1233db944395159916009
Pinned vLLM:      84030bbe3d74d99bad477a3d2e37a973ccd8865c
Base route:       DFlash or eligible DSpark, single dense GQA/FIA group,
                  STANDARD device, sync, single topology, no prefix,
                  FULL or FULL_DECODE_ONLY as source permits
Activation:       VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1
Public support:   frozen
```

The experiment flag is not a product flag. Never reuse its traces as performance evidence because instrumentation deliberately performs host-visible snapshots.

## Preflight

Before any launch, record:

- machine/node and exact Ascend device family/model;
- driver, CANN, PyTorch, torch-npu, Python, vLLM, and vllm-ascend versions;
- both Git SHAs/trees and clean status;
- model and draft model resolved paths/checksums;
- method, W, K/query width, backend, gid, graph mode, topology, async/prefix flags;
- expanded launcher argv and relevant environment;
- available HBM and process isolation;
- destination artifact directory.

Reject the campaign if vLLM or vllm-ascend differs from the recorded identity, the device is COMPATIBILITY/310P, or the route falls outside the candidate validator.

## Artifact Layout

```text
campaign/
  00_preflight/
  G1_capture/
  G2_refresh/
  G3_read_oracle/
  G4_write_oracle/
  G5_timeline/
  G6_tp/
  G6_async/
  G6_prefix/
  G6_chunked_mixed/
  G6_multi/
  G6_dsa/
  G6_dsacp/
  G6_complex/
  G6_eagle3/
  summary/
```

Store raw logs/traces, parsed JSON/CSV, commands, configs, profiler output, and a decision file for every case. Do not commit raw company artifacts to the public source repository.

## Common A/B Protocol

For each valid route use the same model, prompt fixture, seed, scheduler limits, topology, and warmup:

- A0: Window CONFIG_OFF baseline;
- A1: configured Window with product Graph gate still proving fail closed;
- B: internal characterization candidate enabled;
- A2: return to baseline/candidate-equivalent A state for A/B/A' overwrite checks.

For correctness, instrumentation is enabled. For performance, use a later production-safe build with observers disabled; the characterization run itself cannot close performance.

## Conditional Execution Rules

```text
G1 fails -> STOP all Graph Window tests.
G1 passes but any of G2-G5 fails -> STOP feature expansion; preserve artifacts.
G1-G5 pass -> independent G6 branches may run.
One G6 branch fails -> record and stop only that branch; independent branches continue.
Unexpected Target/slot/write mutation -> STOP entire campaign immediately.
Crash/resource/config error -> INFRA, never expected gate or correctness PASS.
```

## G1 — Captured Operand Address

### Goal

Prove the actual captured Draft attention operator/task binds the persistent candidate carrier, not the dummy/full/Target table.

### Cases

- DFlash K+1, short and long context;
- DSpark `sample_from_anchor=True` (K);
- DSpark `sample_from_anchor=False` (K+1);
- FULL and FULL_DECODE_ONLY only where the source route is valid.

### Required evidence

- candidate capture identity and descriptor;
- recorder G1 table/exact/upper addresses;
- backend/task/operator operand addresses from NPU trace;
- full canonical and Target addresses for negative comparison;
- slot/position/query addresses.

### PASS

Actual Draft read operands equal the candidate persistent backing and do not alias Target/canonical/temporary storage. Slot/positions/query remain full. If operator address cannot be observed, G1 is OPEN, not PASS.

## G2 — Runtime Persistent Content Refresh

### Goal

Prove stable addresses carry current-generation content before each replay.

### Fixtures

- A/B/A' with distinct block-table contents;
- exact boundary and non-boundary;
- request reorder/finish-add if base route permits;
- same storage pointer with mapping epoch increment.

### Evidence

For each generation: generation/mapping/request fingerprint, descriptor, table address, table content, exact/upper, replay submission, and completion.

### PASS

Addresses remain stable, contents follow A/B/A', stale identities are rejected, and no future generation overwrites a pending consumer.

## G3 — Physical-read Oracle

### Goal

Prove actual Draft attention physical reads equal the CPU-visible Window oracle.

### Cases

- context <= W;
- exact block boundary;
- non-boundary;
- long context;
- source shortage negative;
- DFlash K+1 and both DSpark widths.

### Evidence

P1 S/E/V, P2 descriptor/valid counts, materialized table/exact/upper, actual operator read-set, and Draft output/proposals if observable.

### PASS

No read outside the intended physical set; all required blocks/columns present; no repeated-window or stale table.

## G4 — Full Write / Target Oracle

### Goal

Prove the read Window does not alter write-side or Target behavior.

### Evidence

Compare OFF versus candidate:

- full canonical table and allocation;
- slot mapping address/content;
- positions/query layout;
- Target metadata identity/content and actual lengths;
- KV write addresses;
- controlled Target logits/output.

### PASS

All listed state remains equivalent within the existing deterministic tolerance. Any Windowed slot or Target mutation is a campaign-stopping bug.

## G5 — Replay / Consumer / Update / Completion Timeline

### Goal

Resolve the effective-generation and lifetime questions that static source cannot answer.

### Evidence

Timestamp/task/event trace for:

```text
materialize N
bind N
metadata build N
replay submit N
consumer start/end N
UPDATE call N
update effective generation
completion event N
retire/reuse N
```

### PASS

The operator consumes generation N, UPDATE attribution matches the actual task semantics, and backing is not reused before device completion. If UPDATE affects N+1, the typed timeline must record that fact and the implementation must still bind current replay safely.

## Base Negative Cases

Confirm zero candidate state or explicit early rejection for CONFIG_OFF, MTP, DeepSeek-V4 co-trained DSpark, eager mode, wrong backend/group/topology, prefix, async, TP>1, mixed phase, Graph descriptor mismatch, stale mapping epoch, and unsupported hardware.

## G6 — Feature Branches

G6 tests run only after corresponding production code exists and passes independent local review. The base candidate by itself must reject them.

### G6-TP / TP16

- per-rank capture identity/provider/address;
- same logical S/E, rank-local physical projection;
- per-rank actual read-set and global union;
- all-rank full slot/write;
- rank generation skew and partial-rank negatives;
- TP16 A/B/A and profiler.

### G6-Async

- two or more inflight generations;
- descriptor × lane × consumer bank;
- delayed and reverse completion;
- abort before/after submit;
- pressure and stale handle;
- real device event proves no early overwrite.

### G6-Prefix

- hit, miss, prefix+tail, gap/overhang;
- eviction and recycled block;
- resident epoch/hold token;
- native/resident/Window intersection;
- A/B/A with actual cache reuse.

### G6-Chunked / Mixed

- long multi-chunk prompt followed by decode;
- first Graph decode sees final source;
- mixed decode+prefill only after owner-approved descriptor/fallback policy;
- no EngineCore-wide abort;
- phase/bucket fingerprint evidence.

### G6-Multi-request

- batch > 1 pure decode;
- reorder, finish/add, same-row replacement;
- in-place mapping rewrite;
- tail reset and bucket transition;
- actual row-to-request oracle and A/B/A'.

### G6-DSA

- captured SAS/SWA/index operands;
- direct-captured derived-state refresh;
- physical read-set and generation equality;
- no-op update timeline;
- compressor/QLI negatives.

### G6-DSA-CP

- global S/E and per-rank local projection;
- per-rank SAS/index/query operands;
- global union oracle;
- communication/completion ordering;
- full write-side invariant.

### G6-SFA / MLA / Multi-group

- run only with separate reviewed adapters;
- enumerate every main/indexer/gid consumer;
- validate actual schema operands, generation, and completion;
- no partial consumer/gid submission.

### G6-Eagle3

- static K >= 3;
- first pass plus every AR step;
- proposal-frozen S and source-derived E_s;
- future column and rejection;
- per-step actual operands/read-set;
- first-pass Target isolation and timeline.

## Performance Follow-up

G1–G5 observers may introduce D2H and synchronization and therefore cannot close latency/throughput gates. After correctness, create a reviewed observer-off candidate and separately measure warmup, TTFT, TPOT, throughput, HBM, CPU memory, D2H/H2D, synchronization, update/event overhead, and contention using A/B/A with raw profiler artifacts.

## Exit Decisions

At session end produce:

| Gate | PASS/FAIL/OPEN/INFRA | Exact evidence | Scope | Next action |
|---|---|---|---|---|
| G1 capture address | | | | |
| G2 refresh/A-B-A | | | | |
| G3 physical reads | | | | |
| G4 write/Target | | | | |
| G5 timeline/lifetime | | | | |
| each G6 branch | | | | |

No result may be generalized across method, query width, backend, device family, topology, async/prefix mode, or commit. Public Graph support remains frozen until owner acceptance and all mandatory route evidence is complete.

