# MRV2 Draft Sliding Window — P7-E NPU Test Matrix

## Evidence boundary

This is the execution matrix for routes locally classified `READY_FOR_NPU`. P7 itself
ran no NPU campaign. A row is not `SUPPORTED` until its exact route has passed the
semantic, physical-read, write/Target, lifetime, and profiler oracles and the result
has been adjudicated into the evidence audit.

Pinned production revisions:

```text
vLLM        84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM-Ascend 4753742ab181920292c504a79eedecf9b428ae1b
Graph       NONE / enforce_eager
```

Every positive launch must also record the hardware profile and resolve
`AttentionBackendFamily.STANDARD`. `COMPATIBILITY` (310P) is a negative Gate, not
a positive campaign. A2 evidence does not close A3/A5, and no STANDARD-family
device is considered supported merely because it is `READY_FOR_NPU`.

The local archive does not contain the expanded server launcher command; it records
only the Node133 script path `/home/wenqing/mrv2_window_test/scripts/qwen3_4b_eagle3_p4b_debug.sh`.
Therefore a campaign must archive the expanded process command before execution.
Inventing a local model path here would violate evidence provenance. The command
contract below is exact except for two mandatory absolute model-path variables that
the server owner must resolve and record.

## Canonical launch contract

```bash
TARGET_MODEL=/absolute/server/path/to/target-model
DRAFT_MODEL=/absolute/server/path/to/draft-model

VLLM_USE_V1=1 \
vllm serve "$TARGET_MODEL" \
  --tensor-parallel-size 1 \
  --pipeline-parallel-size 1 \
  --enforce-eager \
  --seed 1024 \
  --speculative-config "{\"method\":\"METHOD\",\"model\":\"$DRAFT_MODEL\",\"num_speculative_tokens\":K}" \
  --additional-config "{\"draft_window_size\":W}"
```

Before launch, the campaign must record `realpath` and content/version identity for
both model variables, the fully expanded command (`ps -ef` or `/proc/<pid>/cmdline`),
all effective parallel/cache/scheduler/compilation configuration, and both git trees.
For OFF/ON A/B, only `draft_window_size` may differ.

The request contract is deterministic: `temperature=0`, `n=1`, fixed prompt token
ids and seed 1024. If an API rejects greedy `n>1`, that is not evidence for or against
the Window feature.

## Positive route matrix

| ID | Method / backend | Required model & config | Geometry | Topology / execution | Existing evidence | Required campaign |
|---|---|---|---|---|---|---|
| E-DFA-01 | normalized DFlash / dense GQA FIA | owner-approved DFlash target+draft pair; `METHOD=dflash`; configured static K; valid W | short, exact boundary, non-boundary, long | single NPU, TP/DP/PP/PCP/DCP/SP=1, no DSA-CP/FlashComm, eager, async false, prefix off | static only | A=OFF/B=ON; prove K+1 query width, descriptor/table/exact/upper, physical Draft read set, full slot/Target equality, lifecycle and profiler |
| E-DSP-01 | eligible non-V4 co-trained DSpark / dense GQA FIA | owner-approved pair; `METHOD=dspark`; `sample_from_anchor` default true | K-width cases | same exact topology | static only | A/B; prove actual K width and same read/write/lifetime oracles |
| E-DSP-02 | eligible DSpark / dense GQA FIA | same, explicit `sample_from_anchor=false` | K+1-width cases | same | static only | A/B; distinguish from default K path and DFlash K+1 |
| E-E3-01 | normalized Eagle3 / dense GQA FIA | Node133 reference: target Qwen3-4B at `/mnt/share/z00841464/model_weights/Qwen3-4B`; draft `eagle3_qwen3_4b` absolute path must be re-recorded; `METHOD=eagle3`, `K=3`, `W=64` | runtime B=128; short, boundary, non-boundary, long, first-pass→3 steps | Node133 A2/910B2, single NPU, TP1 serialized eager, async/prefix off | scoped single-request L3+L4 from P4b at old final SHA; not new P7 evidence | rerun at P7 SHA; frozen S, each E/V, FullSource refresh, physical operand/read set, target/write, event lifetime, profiler |
| E-E3-02 | Eagle3 static K | same model route | request reorder, finish/add, A→B→A', same-row replacement | exact topology | sequential A→C→A output/isolation evidence; actual row reuse not observed | construct/observe true persistent-row reuse and mapping epoch/fingerprint isolation |
| E-E3-03 | Eagle3 static K | same | controlled batch>1 pure decode | exact topology | target batch not constructed; mixed abort observed | construct batch without scheduler hack or document blocker; verify per-row table/read/Target isolation |

## Semantic and physical oracles required for every positive row

| Oracle | Required record / pass criterion |
|---|---|
| policy | exact decision and topology fingerprint equal expected route |
| math | CPU independently computes `L0/K/H/S/E/V` or parallel-query equivalent |
| source | descriptor and valid counts identify canonical FullSource columns |
| table | materialized active rows equal independent canonical slice; tail deterministic |
| exact/upper | device exact, CPU exact, CPU upper share generation and satisfy builder contract |
| physical read | actual Draft attention operator/task operand and read interval equal oracle |
| write | positions/query/slot mapping and physical KV write identical OFF/ON |
| Target | Target metadata identity/content/length/logits unchanged under controlled state |
| output | deterministic OFF/ON result compared; equality is supporting, not sole evidence |
| lifecycle | no workspace/table/derived-buffer overwrite before real consumer completion |
| performance | D2H/H2D, synchronization, kernel, memory, throughput/latency delta recorded |

## Boundary/event cases

1. `H <= W` short history.
2. exact alignment boundary.
3. non-boundary anchor.
4. long history with bounded backing.
5. Eagle3 first pass and at least K=3 steps.
6. future physical column crossing.
7. rejection in same block.
8. cross-boundary rejection, or an explicit `INSUFFICIENT_EVIDENCE` result after a bounded fixture search.
9. reorder.
10. finish/add and actual same-row replacement.
11. profile/dummy startup baseline behavior.

## Negative-gate campaign

The following are expected rejection/baseline cases, not positive support tests:

| Route | Expected status / behavior |
|---|---|
| CONFIG_OFF | baseline, zero P7/P3 state |
| MTP | FORCED_OFF, baseline, zero Window state |
| DeepSeek-V4 co-trained DSpark | FORCED_OFF, warning/baseline, zero Window state |
| plain Eagle | OWNER_BLOCKED / fail before Window state |
| Eagle3 dynamic-K | OWNER_BLOCKED / fail before proposal state |
| DFlash2 | FAIL_CLOSED |
| DSA/SFA/MLA/V4/V4.1/native/recycling | FAIL_CLOSED before FullSource |
| homogeneous multi-group | FAIL_CLOSED |
| heterogeneous multi-group | OWNER_BLOCKED |
| TP/DP/PP/PCP/DCP>1, SP, DSA-CP, FlashComm | FAIL_CLOSED |
| async true | STATIC_READY but live materialization fails before FullSource |
| prefix cache | FAIL_CLOSED |
| FULL/FULL_DECODE_ONLY/PIECEWISE | Graph Track frozen; FAIL_CLOSED |
| mixed prefill/decode | OWNER_BLOCKED and release blocker; must not be normalized into a pass |
| 310P / `AttentionBackendFamily.COMPATIBILITY` | Window FAIL_CLOSED before FullSource; the 310P patch delegates non-MTP startup to the baseline speculator factory |

## Future async campaign (not currently READY_FOR_NPU)

Async moves from `STATIC_READY` only after a production event/binding design is
reviewed. Its later campaign must include 2+ in-flight generations, delayed and
reverse completion, pool pressure, preempt/resume, abort before/after submit,
exception, finish/add/reorder/row replacement, no early overwrite, derived-buffer
lifetime, and profiler timing. Host fake-token tests are not substitutes.

## Result record format

Every run must publish:

```text
machine/device/firmware/driver/container
vLLM SHA/tree/path
vLLM-Ascend SHA/tree/path
model realpaths and hashes/revisions
fully expanded command and environment
effective config dump and topology fingerprint
request fixture/token ids/sampling/seed
semantic/table/slot/Target/operator/event/profiler artifacts
raw logs and SHA256 index
PASS / FAIL / INSUFFICIENT_EVIDENCE per oracle
```

No row in this document closes release by itself.

## Independent Review Resolution

F-01 is `ACCEPTED` after the P8 delivery source recheck corrected the P7 rationale.
The final campaign schema includes the semantic hardware family and an explicit 310P
negative test. `_init_speculator_310p` delegates non-MTP methods to the baseline
factory; therefore the new COMPATIBILITY family Gate—not a general MTP-only startup
rule—protects the Window capability boundary against class-subtyping drift.

F-02/F-03 are host-contract fixes: NPU async campaigns must additionally verify
derived-buffer non-alias/lifetime and exact topology continuity. They do not turn
async into a positive row.

```text
P7-E NPU: NOT VERIFIED
READY_FOR_NPU: exact campaign candidates only
ASYNC NPU: NOT READY
G-MIXED: OWNER_BLOCKED / RELEASE_BLOCKER
GRAPH TRACK: FROZEN
```

