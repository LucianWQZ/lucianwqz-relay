**# P7-X Graph Base G1–G5 — Ascend A3 Device Characterization**


Date: 2026-10-17

Host: node-39-101

Mode: MRV2 HARD-GATED / TEAM-TOOL ASSISTED

Candidate: `LucianWQZ/vllm-ascend` @ `8cb4bed670f395c257c1233db944395159916009`


**---**


**## 1. Executive summary**


The campaign reached the real Ascend A3 device with verified MRV2, a valid

single-die TP1 fixture, an active Draft Window (W=1024), and the internal

Graph characterization switch enabled.


The candidate installed the characterization provider and completed startup

ACL Graph capture, recording six CAPTURE events across the three registered

capture buckets plus one MATERIALIZED runtime generation.


The first real draft replay then failed deterministically:


```

ValueError: Draft metadata mutable storage aliases Target metadata

```


The failure occurs inside `bind_read_carrier`, before any BOUND / REPLAY /

CONSUMER event. No actual NPU task operand address was observed, and no

replay/update/completion timeline exists.


```

BASE_GRAPH_DEVICE_ARCHITECTURE = FAIL

NEXT_ACTION = RETURN_TO_LOCAL_CODEX

```


The public Graph Window gate remains frozen (proved independently by control A1).


**---**


**## 2. Hard-gate compliance**


| Rule | Result |

|---|---|

| MRV2 required, not MRV1 | PASS: in-worker `NPUModelRunner` v2 + `AscendDSparkSpeculator` |

| env alone is not evidence | PASS: class objects read from the live in-process worker |

| `VLLM_USE_V2_MODEL_RUNNER=1` | SET for every positive service |

| TP1 / DP1 / PP1 / PCP1 / DCP1 | PASS |

| async OFF | PASS (`async_scheduling=False`) |

| prefix OFF | PASS (`enable_prefix_caching=False`) |

| SP / DSA-CP / FlashComm OFF | PASS |

| STANDARD dense FIA single group | PASS (runtime policy accepted) |

| FULL / FULL_DECODE_ONLY | PASS (`FULL_DECODE_ONLY`) |

| W=1024 | PASS |

| no server source modification | PASS |

| no public support-matrix change | PASS |

| no gate deletion / hot patch | PASS |


Invalid-run guard: the driver refused to continue unless the live worker class

was `vllm_ascend.worker.v2.model_runner.NPUModelRunner` and the live speculator

was an Ascend V2 DSpark/DFlash class.


**---**


**## 3. Exact source and runtime identity**


**### Source**


| Component | SHA | Tree |

|---|---|---|

| vllm-ascend | `8cb4bed670f395c257c1233db944395159916009` | `899899c23fdc87acaed49c889eecd1f7889ad9c4` |

| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |


Both working trees were clean. The characterization commit subject is

`spike(spec-decode): prepare graph window characterization`.


**### Delta from the performance commit**


`1b7215c37d1e3c9d1edac1fc20bcad26917ca251` → `8cb4bed6` changes 13 Python

files (2378 insertions, 50 deletions). There are ****no**** C++, CANN op, native

`.so`, ABI, CMake, setup or build-system changes. The Node101-local A3 native

donor was therefore reused.


**### Runtime overlay**


- Overlay: `/home/wenqing/mrv2_graph_g1g5/runtime/graph_char_overlay`

- Python payload: exact `8cb4bed6` source `.py` (617 files)

- Non-Python payload: A3 donor from `/home/wenqing/vllm-ascend-main` (1269 files)

- `vllm` is a symlink to the pinned checkout

- Import provenance proved both `vllm` and `vllm_ascend` resolve inside the

  overlay; legacy trees are blocked by `runtime/site/sitecustomize.py`.


Key module hashes:


| Module | SHA256 |

|---|---|

| `draft_window_graph_characterization.py` | `2ece48cf77179db14d4d4fee31fb255984579f9d13749b002002e7fe68e15843` |

| `dflash/capture.py` | `f26d579a2d7c3d44d63122bc82f5def0fc761a6002d58017780d51062d883ccb` |

| `draft_window_graph.py` | `d53e3c78a4c25ecba072fc1ab40337afa88d2945f40ddcd1cc4433dbbc8284c6` |

| `draft_window.py` | `dd8ebbfc65c1009a2bfe8ff1b2e2435b0d1333ffc1fa930be47b1c896fb8b5b2` |


**---**


**## 4. MRV2 runtime identity (in-worker proof)**


Read from the live in-process engine object graph, not from env markers:


```

model_runner_class = vllm_ascend.worker.v2.model_runner.NPUModelRunner

speculator_class   = vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator

method             = DSpark

policy_state       = DraftWindowPolicyState.ELIGIBLE_ON

effective_window   = 1024

graph_mode         = FULL_DECODE_ONLY

TP                 = 1

async              = False

prefix             = False

```


Log markers corroborate:


- `WARNING worker.py:497 npu model runner v2 is in developing`

- `INFO speculator.py:144 Capturing model for DSpark speculator...`


MRV1 did not participate. Evidence: `G0_mrv2_identity/identity.json`,

`negative/A0/result.json`, `negative/B/result.json`.


**---**


**## 5. Fixture**


```

main   = /mnt/share/wql/Qwen3-8B                  (bf16, complete, 16 GiB)

draft  = /mnt/share/dspark_qwen3_8b_block7        (DSpark, 4.4 GiB)

method = dspark, K=7, query width=7

layout = dense GQA 32 heads / 8 KV heads, head_dim 128, 36 target layers

draft target layers = [1, 9, 17, 25, 33]

backend = AscendAttentionBackendImpl / STANDARD single FIA group

```


This is the exact TP1 fixture used by

`tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_8b_dspark.py`.

The DFlash fallback `z-lab/Qwen3-8B-DFlash-b16` exists on disk but has no

weights, so it is not a runtime fixture.


```

BASE_G1_G5_FIXTURE = QWEN3_8B + DSPARK_QWEN3_8B_BLOCK7 (TP1)

```


Details: `G0_fixture/fixture_inventory.md`, `manifests/fixture.json`.


**---**


**## 6. Controls**


Same fixture, same prompt, same seed.


| Control | Window | Flag | Result |

|---|---|---|---|

| A0 | OFF | 0 | OK. MRV2 graph baseline produced 16 deterministic tokens. No characterization/provider state. |

| A1 | 1024 | 0 | EXPECTED_REJECT. `GRAPH_FROZEN` before materialization. Public Graph Window gate closed. |

| B | 1024 | 1 | CANDIDATE_RUNTIME_FAILURE at first bind after successful capture. |


A1 message (source fact):


```

MRV2 Draft Window P7-X route rejected before materialization:

status=GRAPH_FROZEN; Graph mode FULL_DECODE_ONLY belongs to the frozen Graph Track

```


A0 proves the fixture, MRV2 runner, DSpark speculator, and ACL Graph baseline are

operational. The failure is specific to the characterization path.


Commands:


```

VLLM_USE_V2_MODEL_RUNNER=1

VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH={0,1}

VLLM_ENABLE_V1_MULTIPROCESSING=0

ASCEND_RT_VISIBLE_DEVICES=\<free die>

python scripts/driver_case.py --case \<A0|A1|B> --window \<off|1024> --flag <0|1> ...

```


`VLLM_ENABLE_V1_MULTIPROCESSING=0` is required only so the driver can read the

in-worker recorder; it is not an MRV2 gate.


**---**


**## 7. G1 — Actual captured operand address**


**### Verdict**


```

G1 = FAIL

```


**### Facts observed**


Startup capture registered three real manager descriptors:


| Bucket | Capture descriptor |

|---|---|

| (1,7) | `mode=FULL;reqs=1;tokens=7;uniform=7` |

| (2,14) | `mode=FULL;reqs=2;tokens=14;uniform=7` |

| (4,28) | `mode=FULL;reqs=4;tokens=28;uniform=7` |


Six CAPTURE events (warmup + capture per bucket) recorded:


| Bucket | Persistent table address | Exact/upper length |

|---|---:|---:|

| (4,28) | 20623361164800 | 1151 |

| (2,14) | 20623361166848 | 1151 |

| (1,7) | 20623361168384 | 1151 |


One MATERIALIZED runtime generation (before copy into the capture backing):


```

generation_id = 0

mapping_epoch = 0

table address = 20623361162752

table row     = [1, 0, 0, ...]

exact length  = 12

upper length  = 12

```


Then `bind_read_carrier` raised:


```

ValueError: Draft metadata mutable storage aliases Target metadata

  draft_window_graph_characterization.py:529 prepare_parallel_...

  draft_window_graph.py:818 bind_read_carrier

  draft_window.py:2585 validate_draft_metadata_isolation

```


No BOUND, REPLAY, CONSUMER, UPDATE or LIVE event was emitted.


**### Why this is FAIL, not OPEN**


The candidate has a deterministic device-side integration defect on a valid

fixture. The capture address contract is not the blocker; the runtime bind is.

Because the bind cannot complete, the actual ACL Graph Draft attention task

operand address is never observed, and no replay can be attributed.


Per rule 22, G1 did not PASS, so G2–G5 were not attempted.


**### Root cause**


`_build_private_graph_metadata` restores the canonical full write/query carriers

onto Draft metadata after isolation:


```python

layer_metadata.slot_mapping = write_side.slot_mapping

layer_metadata.positions = write_side.positions

layer_metadata.query_start_loc = write_side.query_start_loc

```


where:


```python

slot_mapping    = owner.block_tables.slot_mappings[gid, :token_count]

positions       = owner.input_buffers.positions[:token_count]

query_start_loc = owner.input_buffers.query_start_loc[:request_count + 1]

```


Immediately afterwards `bind_read_carrier` calls

`validate_draft_metadata_isolation(metadata, target_metadata=...)`, which rejects

any mutable storage shared with Target metadata.


On the real path, Target metadata is built from the same canonical objects:

`build_slot_mappings_by_layer` stores the same tensor object for every layer;

Target `positions` / `query_start_loc` come from the same `InputBuffers`.

Therefore the candidate's own two invariants contradict each other:


- "Draft metadata must use the canonical full write carriers";

- "Draft metadata must share no mutable storage with Target metadata".


The CPU UT uses a synthetic `_target_metadata()` with independent tensors, so it

passes and does not catch the real integration contradiction.


This is a ****candidate defect****, not an environment defect. No server source

patch was applied (rule 28).


**---**


**## 8. G2–G5 status**


| Gate | Verdict | Reason |

|---|---|---|

| G2 Persistent refresh | OPEN | Blocked by G1; no A/B/A' generation, no stable-address/content check |

| G3 Physical read oracle | OPEN | Blocked by G1; candidate also has no NPU read-set observer |

| G4 Full write / Target isolation | OPEN | Blocked by G1; A0/A1 controls only, no OFF-vs-ON write comparison |

| G5 Timeline / lifetime | OPEN | Blocked by G1; no NPU trace. Source itself says `assert_update_effective_for` requires NPU timeline evidence |


Unknown by construction:


```

EFFECTIVE_GENERATION_MAPPING = UNKNOWN

DEVICE_COMPLETION_OWNER      = UNKNOWN

EARLIEST_SAFE_CARRIER_REUSE  = UNKNOWN

```


**---**


**## 9. Negative matrix**


Device:


- A0 CONFIG_OFF → zero characterization state, baseline OK.

- A1 flag OFF → public Graph gate closed (`GRAPH_FROZEN`).

- B flag ON → candidate runtime failure at bind.

- B_DFLASH → fixture unavailable (no weights).


CPU: 31/31 expected outcomes matched, covering strict flag parsing; CONFIG_OFF;

MTP forced off; DeepSeek-V4 DSpark forced off; plain Eagle and unknown method

rejection; eligible DFlash/DSpark; graph NONE/PIECEWISE rejection; async, TP/DP/

PP/PCP/DCP>1, SP, DSA-CP, FlashComm, prefix and COMPATIBILITY backend rejection;

window arithmetic and dynamic-K rejection.


Full table: `negative/README.md`, `negative/negative_matrix_cpu.json`.


**---**


**## 10. Decision and next action**


```

G1 CAPTURE ADDRESS            = FAIL

G2 PERSISTENT REFRESH         = OPEN

G3 PHYSICAL READ              = OPEN

G4 FULL WRITE / TARGET        = OPEN

G5 TIMELINE / LIFETIME        = OPEN


BASE GRAPH DEVICE ARCHITECTURE = FAIL

PUBLIC GRAPH SUPPORT           = STILL FROZEN

SERVER SOURCE MODIFICATIONS    = NONE

NEXT ACTION                    = RETURN_TO_LOCAL_CODEX

```


Required local work before re-running the device campaign:


1. Resolve the isolation/write-side contradiction in the candidate.

   Two consistent designs:

   - exclude the explicitly immutable full write/query carriers from the

     isolation oracle, while separately asserting they are exactly the canonical

     carriers (already done by `_validate_metadata_uses_carrier`); or

   - validate isolation on the Draft-private metadata before restoring the

     canonical write carriers, and keep the two assertions separate.

2. Add a device-faithful UT whose Target metadata shares the real canonical

   `block_tables.slot_mappings`, `input_buffers.positions` and

   `input_buffers.query_start_loc` objects, so the CPU suite cannot pass while

   the real path fails.

3. Re-run G1 on node-39-101 with the same fixture, then G2–G5 in order.


Do not relax the public Graph Window gate as part of the fix.


**---**


**## 11. Evidence discipline**


| Claim | Class |

|---|---|

| Source SHAs/trees | SOURCE FACT |

| No native delta | SOURCE FACT |

| Import provenance | HOST/RECORDER FACT |

| MRV2 runner/speculator classes | HOST/RECORDER FACT (live worker objects) |

| Capture backing addresses/lengths | HOST/RECORDER FACT |

| Bind exception and traceback | HOST/RECORDER FACT |

| Actual NPU task operand equality | NOT OBSERVED |

| Physical read set | NOT OBSERVED |

| Effective update generation / completion owner | NOT OBSERVED |

| Root-cause mechanism | INFERENCE from source + recorded objects |


No output-correctness claim is used as evidence of physical reads.


**---**


**## 12. Integrity and cleanup**


- Original team tools: 2296 files before/after, identical hashes →

  `ORIGINAL_TEAM_TOOLS_UNCHANGED`.

- No campaign vLLM / benchmark / driver process remains.

- HBM released; `00_preflight/npu_after.txt` saved.

- No server source file edited.

- One transparency note: the target commit object was fetched into the `.git`

  object store of the read-only prior tree `/home/wenqing/mrv2_p7x_perf_final/src/vllm-ascend`

  to seed the independent campaign clone. No checkout, reset, delete, overwrite,

  ref change or working-tree change was made there; `git status --porcelain` was

  and remains empty. All campaign work uses the new independent clones under

  `/home/wenqing/mrv2_graph_g1g5/src/`.
