# P7X_A3_04_A0_A1_B_Record

RUN_ID: `20261019_055109_13373fff`  
All commands and exit codes: `P7X_A3_02_Execution_Record.md`.

---

## 0. Common contract

| Field | Value |
|---|---|
| Target | `/mnt/share/wql/Qwen3-8B` |
| Draft | `/mnt/share/dspark_qwen3_8b_block7` |
| method | dspark |
| K | 7 |
| query width | 7 |
| window W | 1024 |
| block span | 128 |
| graph mode | FULL_DECODE_ONLY (decode descriptor FULL) |
| topology | TP1 DP1 PP1 PCP1 DCP1 |
| async / prefix / SP / DSA-CP / FlashComm | OFF |
| runner | `vllm_ascend.worker.v2.model_runner.NPUModelRunner` |
| speculator | `vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator` |
| prompt | `Hello, my name is` |
| seed | 0 |
| temperature | 0.0 |
| ignore_eos | true |
| max_tokens | 16 |
| max_model_len | 4096 |
| max_num_seqs | 4 |
| max_num_batched_tokens | 4096 |
| gpu_memory_utilization | 0.80 |
| device | logical die 5 (verified via `torch.npu.mem_get_info`) |

Environment per case:

```text
VLLM_USE_V2_MODEL_RUNNER=1
VLLM_ENABLE_V1_MULTIPROCESSING=0
VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=<0 for A0/A1, 1 for B>
VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=<B only>
```

---

## 1. A0 — window OFF, experimental flag 0

Command: `CMD-0017`, case `A0`, attempt 1, device 5.

Actual argv (driver):

```text
--case A0 --window off --flag 0 --out <run_root>/A0/result.json
```

Compilation:

```text
cudagraph_mode=FULL_DECODE_ONLY
cudagraph_capture_sizes=[7,14,28]
```

### Expected

- engine normal;
- MRV2 runner/speculator correct;
- Graph baseline executes;
- deterministic output matches the old contract;
- zero characterization session/provider/carrier;
- no v2 artifact.

### Actual

```text
status = OK
model_runner_class = vllm_ascend.worker.v2.model_runner.NPUModelRunner
speculator_class = vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator
policy_state = None
characterization_installed = false
provider_installed = false
```

Output token ids:

```text
[8515, 11, 323, 358, 1079, 264, 220, 17, 18, 4666, 6284, 5458, 13, 358, 614, 1012]
```

Output text:

```text
" Alex, and I am a 23-year-old student. I have been"
```

This matches the previous campaign's A0 token ids exactly.

Evidence: `A0/result.json`, `A0/driver.log`.

### Verdict

```text
A0 = PASS
```

Scope: device execution; identity + deterministic output contract. It does not prove any Window/Graph operand.

---

## 2. A1 — window W=1024, experimental flag 0

Command: `CMD-0018`, case `A1`, attempt 1, device 5.

Actual argv:

```text
--case A1 --window 1024 --flag 0 --out <run_root>/A1/result.json
```

### Expected

`GRAPH_FROZEN`, before Window FullSource/workspace/provider/capture carrier creation.

### Actual

```text
status = EXCEPTION
exception_type = NotImplementedError
exception_message = MRV2 Draft Window P7-X route rejected before materialization:
  status=GRAPH_FROZEN; Graph mode FULL_DECODE_ONLY belongs to the frozen Graph Track
```

Exact traceback path:

```text
examples? no
driver_case.py:76 LLM(...)
vllm/entrypoints/llm.py:343
vllm/v1/engine/core.py:145 _initialize_kv_caches
vllm_ascend/worker/worker.py:1144 initialize_from_config
vllm_ascend/worker/v2/model_runner.py:260 initialize_kv_cache
vllm/v1/worker/gpu/model_runner.py:703 set_attn
vllm_ascend/worker/v2/spec_decode/dspark/speculator.py:198 _initialize_draft_window_source_capability
vllm_ascend/worker/v2/spec_decode/draft_window.py:1503 _build_draft_window_source_capability_for_context
vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py:138 require_local_materialization
```

The failure occurs inside `build_draft_window_source_capability`, before:

- FullSource creation;
- workspace creation;
- provider installation;
- capture carrier installation.

`characterization_installed` / `provider_installed` fields are `null` because the driver never obtained a constructed speculator (LLM construction failed). The early-gate proof is the exception location and message, not a zero-state object inspection.

Evidence: `A1/result.json`, `A1/driver.log`; rc=2 is the expected gate exit.

### Verdict

```text
A1_EARLY_GRAPH_FROZEN = PASS
PUBLIC GRAPH SUPPORT = STILL FROZEN
```

---

## 3. B — fixed contract, window W=1024, experimental flag 1

Command: `CMD-0019`, case `B`, attempt 1, device 5.

Actual argv:

```text
--case B --window 1024 --flag 1 \
--capture-sizes 7,14,28 \
--artifact <run_root>/B/artifact/B_artifact.json \
--out <run_root>/B/result.json
```

Environment:

```text
VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1
VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=<artifact>
```

### Expected

- new build/bind/publish path;
- Target metadata non-empty;
- legal canonical sharing accepted;
- private read isolated;
- W=1024 effective;
- no eager fallback;
- first bind and real replay occur;
- v2 artifact with capture/operand/G4/lifecycle records.

### Actual

```text
status = EXCEPTION
exception_type = RuntimeError
exception_message = capture operand observer is already attached
```

First divergence:

```text
vllm_ascend/worker/v2/spec_decode/dflash/capture.py:376
  attach_parallel_graph_capture_operand_observer(...)
vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py:1006
  raise RuntimeError("capture operand observer is already attached")
```

The first capture descriptor `(4,28)` recorded a capture event; a later descriptor's metadata reused the same layer metadata object and the observer context attribute was still attached.

### Partial artifact

`B/artifact/B_artifact.json`:

| Section | Count |
|---|---|
| events | 1 |
| operand_events | 0 |
| g4_records | 0 |
| lifecycle_events | 0 |

Schema: `mrv2-draft-window-graph-characterization-v2`.

Capture event:

| Field | Value |
|---|---|
| stage | capture |
| route | dspark |
| descriptor | `mode=FULL;reqs=4;tokens=28;uniform=7;max_query=None;loras=0;ubatches=1` |
| backing_table_address | 20623361164800 |
| exact_lengths | [1151, 1151, 1151, 1151] |
| upper_lengths | [1151, 1151, 1151, 1151] |
| slot_mapping_address | 20623361145856 |
| slot_mapping_values | -1 × 28 |
| positions_address | 20623359230464 |
| position_values | 0 × 28 |
| query_layout_address | 20623359268352 |
| query_layout_values | [0, 7, 14, 21, 28] |
| generation_id / mapping_epoch | null / null |

### Old fix point

```text
B_OLD_FIX_POINT = NOT_REACHED
```

The old failure was in `bind_read_carrier` → `validate_draft_metadata_isolation`. This run never reached bind. Therefore:

```text
B_BIND_PUBLISH = NOT_RUN
B_REAL_REPLAY = NOT_RUN
ALIAS_FIX_DEVICE = NOT_REACHED
```

Host-level alias fix evidence is separate: `test_real_target_metadata_sharing_is_allowed_for_full_write_carriers` and `test_draft_private_fields_still_reject_target_storage_alias` both PASS (`host_tests/real_owner_regression.log`). This is not device evidence.

Evidence: `B/result.json`, `B/driver.log`, `B/artifact/B_artifact.json`.

### Verdict

```text
B_FIXED_CONTRACT = FAIL (new production defect at capture observer re-attach)
OLD_ALIAS_FAILURE = NOT_REPRODUCED (not reached)
```

---

## 4. Diagnostic capture-inventory attempts (not fixed-contract evidence)

These attempts were made only to localize the capture failure. They are explicitly
`DIAGNOSTIC_PARTIAL_INVENTORY_NOT_FIXTURE_CONTRACT` and must not be counted as
Base G1–G5 evidence.

| Case | capture sizes | prompts | max_tokens | Result | Meaning |
|---|---|---|---|---|---|
| `B_DIAG_CAP7` | [7] | 1 | 16 | OK, but only materialized/retired events; no capture/bound/replay | target manager had no capture descriptor; draft never captured (eager) |
| `B_DIAG_CAP14` | [14] | 2 | 16 | OK, same eager-only artifact | target manager had no capture descriptor |
| `B_DIAG_CAP28` | [28] | 4 | 16 | OK, same eager-only artifact | target manager had no capture descriptor |
| `B_DIAG_CAP28_INTROSPECT` | [28] | 4 | 1 | OK; target `needs_capture=false`, `_capture_descs={}`; draft `needs_capture=true`, descriptor (4,28) | `capture_model` returns early on target manager, so Draft capture is never invoked |
| `B_DIAG_CAP24_INTROSPECT` | [24] | 4 | 1 | RuntimeError: Graph characterization requires real manager capture descriptors | draft manager had no descriptors at characterization install |

The fixed contract `[7,14,28]` is the only configuration that installs the
characterization session and enters the draft capture path; it fails at the
observer re-attach.

Evidence: `B/diag_cap7/`, `B/diag_cap14/`, `B/diag_cap28/`,
`B/diag_cap28_introspect/`, `B/diag_cap24_introspect/`.

---

## 5. Attempt summary

| Case | CMD | Attempt | Device | Exit | Status |
|---|---|---|---|---|---|
| A0 | CMD-0017 | 1 | 5 | 0 | OK |
| A1 | CMD-0018 | 1 | 5 | 2 expected | GRAPH_FROZEN |
| B fixed | CMD-0019 | 1 | 5 | 2 | capture observer re-attach |
| B diag cap7 | CMD-0020 | 1 | 5 | 0 | eager-only diagnostic |
| B diag cap14 | CMD-0021 | 1 | 5 | 0 | eager-only diagnostic |
| B diag cap28 | CMD-0022 | 1 | 5 | 0 | eager-only diagnostic |
| B diag cap28 introspect | CMD-0023 | 1 | 5 | 0 | inventory only |
| B diag cap24 introspect | CMD-0024 | 1 | 5 | 2 | install rejects empty draft descriptors |

No attempt overwrote another attempt's directory.
