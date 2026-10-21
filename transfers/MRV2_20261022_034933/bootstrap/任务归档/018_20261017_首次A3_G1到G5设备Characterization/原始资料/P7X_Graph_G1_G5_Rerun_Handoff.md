# P7-X Graph Base G1-G5 A3 Rerun Handoff

Date: 2026-10-17  
Purpose: rerun the same accepted Base Graph fixture after the A3 alias-contract repair  
New local candidate commit: `13373fff637e819f3db125e05064f94cba3475a3`  
Tree: `739cde3de61e65be7cdbd187baebb6d17da04aee`  
Parent: `8cb4bed670f395c257c1233db944395159916009`

> This commit has intentionally **not** been pushed. Transport or publish it
> through the owner-approved process before the server run, then verify the
> exact SHA and tree below. Do not reconstruct the fix manually on Node101.

## 1. Do not rediscover the fixture

Reuse exactly:

| Field | Required value |
|---|---|
| machine family | Ascend A3; original run was `node-39-101`, CANN 9.1.0, driver 26.0.rc1 |
| target | `/mnt/share/wql/Qwen3-8B` |
| draft | `/mnt/share/dspark_qwen3_8b_block7` |
| runner | `vllm_ascend.worker.v2.model_runner.NPUModelRunner` |
| speculator | `vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator` |
| method | `dspark` |
| K / query width | `7 / 7`, default `sample_from_anchor=True` |
| backend | `AscendAttentionBackendImpl`, STANDARD dense FIA, one group |
| Graph | `FULL_DECODE_ONLY` (decode descriptors are FULL) |
| W | `1024` |
| block size / capacity | `128 / 1151` tokens |
| topology | TP1 DP1 PP1 PCP1 DCP1 |
| disabled | async, prefix, SP, DSA-CP, FlashComm |
| capture sizes | `[7,14,28]`, buckets `(1,7)`, `(2,14)`, `(4,28)` |

The rejected DFlash fixture still lacks weights and must not replace this
accepted DSpark fixture.

## 2. Fixture hashes

Verify before running:

| File | SHA256 |
|---|---|
| target `config.json` | `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30` |
| target `model.safetensors.index.json` | `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc` |
| target `tokenizer.json` | `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4` |
| draft `config.json` | `e470e70a553616f0dce8f783f42cfd25b7bd7dfdcd57ead680a0623040725611` |
| draft `model.safetensors` | `5c922d1f96c8d18dbdf005c40ea99878d9133d70eaa3be4bd1077ee5f2afc1e5` |

Use the existing `manifests/fixture_hashes.txt` for all target shards and keep
the same prompt and prompt hash.

## 3. Source identity gate

Before any NPU run:

```bash
cd <vllm-ascend-checkout>
git rev-parse HEAD
git rev-parse HEAD^{tree}
git status --porcelain --untracked-files=all
```

Required:

```text
HEAD = 13373fff637e819f3db125e05064f94cba3475a3
tree = 739cde3de61e65be7cdbd187baebb6d17da04aee
status = clean
```

Pinned vLLM must be:

```text
SHA  = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status = clean
```

Stop if any identity differs.

## 4. Required environment

Preserve the original in-process driver setup:

```bash
export VLLM_USE_V2_MODEL_RUNNER=1
export VLLM_ENABLE_V1_MULTIPROCESSING=0
export ASCEND_RT_VISIBLE_DEVICES=<same free logical die policy>
```

For B/G1-G5 only:

```bash
export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1
export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=<campaign>/G1_G5_characterization_v2.json
```

For A0/A1, the internal experimental flag must remain `0`/unset exactly as in
the first campaign.

`VLLM_ENABLE_V1_MULTIPROCESSING=0` is only for recorder access. It is not an
MRV2 capability gate.

## 5. Driver

Reuse the original archived `commands/driver_case.py`; do not hand-author a new
fixture loader. The stable invocation shape remains:

```bash
python scripts/driver_case.py \
  --case <A0|A1|B> \
  --window <off|1024> \
  --flag <0|1> \
  <the same expanded arguments captured by the first campaign>
```

Copy the exact expanded argv, prompt, seed, max tokens, model paths and runtime
environment from the first campaign artifact index.

## 6. Mandatory run order

### A0 — Window OFF baseline

```text
window=off
experimental flag=0
```

PASS:

- engine starts;
- same deterministic output contract as first A0;
- zero Draft Window characterization/provider state;
- no v2 artifact emitted;
- Graph baseline remains functional.

STOP if baseline output or startup regresses.

### A1 — public gate control

```text
window=1024
experimental flag=0
```

PASS is the expected early rejection:

```text
GRAPH_FROZEN
```

STOP if public Graph Window executes or materializes state.

### B — internal characterization

```text
window=1024
experimental flag=1
artifact path set
```

The old bind exception must not occur. Startup capture, runtime materialize,
bind, replay, consumer and update records must all be present before continuing
to gate adjudication.

STOP on any alias exception, carrier mismatch, descriptor mismatch, missing
record, Target mutation or stale generation.

## 7. G1 — operand binding

Required artifact fields:

- all expected capture descriptors;
- `capture_operator` event for the active descriptor;
- `update_operator` event for the runtime generation;
- expected, captured and actual table addresses;
- length kind/address/values;
- backend, layer, consumer, handle/event/stream identity;
- generation/mapping epoch for update.

PASS:

```text
expected backing ptr == capture operator table ptr
expected backing ptr == update operator table ptr
descriptor/backend/consumer match the selected route
```

Additionally capture CANN/task evidence if the installed tooling exposes the
internal task operand. Host/operator-boundary equality alone must be labelled
as such.

## 8. G2 — A/B/A'

Run three generations on the same persistent backing:

```text
A  : generation g,   mapping epoch e,   content A
B  : generation g+1, mapping epoch e+1, content B, B != A
A' : generation g+2, mapping epoch e+2, content A, identity != A
```

PASS:

- same table address for A/B/A';
- A and A' content equal;
- B differs;
- stale A cannot authorize A';
- table and length generations match at every bound/update record;
- no early overwrite while the previous device consumer is pending.

Run:

```bash
python tools/p7x_graph_g1_g5.py audit \
  <campaign>/G1_G5_characterization_v2.json \
  --output <campaign>/G1_G5_audit.json
```

## 9. G3 — independent oracle and device boundary

For each short/boundary/non-boundary/long case, extract the canonical full row,
H, E, upper, valid block count and geometry from the runtime record. Invoke:

```bash
python tools/p7x_graph_g1_g5.py oracle \
  --full-table <comma-separated canonical row> \
  --horizon <H> --exact <E> --upper <upper> --window 1024 \
  --legacy-block-size <legacy B> --block-span 128 \
  --query-width 7 --valid-block-count <count> \
  --output <case>/independent_oracle.json
```

PASS requires the operator-boundary table/length to equal the independent
oracle and a CANN/msprof/msprobe artifact correlated to the FIA task. If the
tool cannot expose physical transactions, report the strongest available
device-boundary fact and keep `PHYSICAL_MEMORY_TRANSACTION=UNPROVEN`.

Source shortage must fail before operator submission.

## 10. G4 — full write/Target oracle

Compare A0 and B machine records. Required:

- canonical full table unchanged;
- slot mapping pointer and values unchanged;
- positions pointer and values unchanged;
- query layout pointer and values unchanged;
- Target metadata root/layer identities unchanged;
- Target read lengths unchanged;
- Draft Window table is private and differs only in read visibility;
- Target output/logits hash equal under the controlled identical input/state,
  when the driver supplies it.

The v2 artifact supplies all fields except that the driver must explicitly pass
the real Target output if a Target hash is required.

## 11. G5 — timeline and lifetime

Collect a task/stream timeline containing:

```text
generation materialized
-> replay submitted event
-> FIA consumer/task
-> update source generation
-> backend update event
-> effective replay generation
-> real device completion
-> lease retirement/reuse
```

PASS requires proof of whether UPDATE(N) affects replay N or N+1, and proof
that backing is not rewritten before the device consumer completes. The host
`PROPOSAL_RETIRED` record is not completion proof. Do not substitute Python
return or global synchronize as the feature contract.

Any characterization-only synchronization used by profiler tooling must be
marked `NOT PERFORMANCE REPRESENTATIVE`.

## 12. Required output bundle

At minimum preserve:

- source SHAs/tree/status;
- environment and fully expanded argv;
- fixture hashes and prompt hash;
- A0/A1/B stdout/stderr and result JSON;
- `G1_G5_characterization_v2.json`;
- `G1_G5_audit.json`;
- independent oracle per case;
- CANN/msprof/msprobe raw output and tool versions;
- task/stream/event timeline;
- G4 OFF/ON comparison;
- final G1-G5 decision table;
- artifact index and SHA256SUMS.

## 13. Stop conditions

Stop the campaign and do not enter Batch A if any of the following occurs:

- A0 regression;
- A1 no longer fails closed;
- source/tree/fixture drift;
- bind/isolation failure;
- missing capture or update operand record;
- table/length generation mismatch;
- canonical write/Target mutation;
- stale A authorizes A';
- device timeline cannot establish safe reuse;
- G1-G5 is not fully adjudicated.

## 14. Scope boundary

Do not implement or claim TP16, Prefix, Eagle3, DSA, MLA, Async, DSA-CP, SFA,
mixed Graph, multi-group runtime, or DFlash2 Graph during this rerun. Batch A
remains blocked until Base G1-G5 passes.

## 15. Handoff verdict

```text
SAME FIXTURE: REQUIRED
NEW CANDIDATE: 13373fff637e819f3db125e05064f94cba3475a3
LOCAL PREPARATION: COMPLETE
NEXT A3 G1-G5 CAMPAIGN: READY
DEVICE GATES: OPEN UNTIL EVIDENCE IS COLLECTED
PUBLIC GRAPH USER GATE: STILL FROZEN
```
