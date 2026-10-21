# Artifact Index — P7-X Graph Base G1–G5

Campaign root: `/mnt/wenqing/mrv2_graph_g1g5_campaign/`  
Working root: `/home/wenqing/mrv2_graph_g1g5/`  
Date: 2026-10-17

## Reports

| Path | Purpose |
|---|---|
| `reports/P7X_Graph_G1_G5_NPU_Characterization.md` | Full English technical report |
| `reports/P7X_Graph_G1_G5_Teacher_Summary_CN.md` | One-page Chinese summary |
| `reports/P7X_Graph_G1_G5_Device_Facts.json` | Machine-readable facts and decision |
| `reports/P7X_Graph_G1_G5_Next_Action.md` | Local fix guidance and re-run acceptance |
| `reports/ARTIFACT_INDEX.md` | This index |
| `/home/wenqing/reference/P7X_Graph_G1_G5_A3_Characterization_CN.md` | Comprehensive Chinese master report |

## Preflight

| Path | Purpose |
|---|---|
| `00_preflight/npu_before.txt` | Host, disk, memory, NPU and process state before |
| `00_preflight/npu_after.txt` | Same after cleanup |
| `00_preflight/import_provenance.txt` | Actual `vllm` / `vllm_ascend` module files, class paths, sys.path |
| `00_preflight/ut_test_draft_window_graph_characterization.log` | UT: PASS 19 |
| `00_preflight/ut_test_draft_window_graph_binding.log` | UT: PASS 37 |
| `00_preflight/ut_test_draft_window_graph_carrier.log` | UT: PASS 46 |

## Manifests

| Path | Purpose |
|---|---|
| `manifests/source_identity.json` | Exact SHAs/trees, cleanliness, delta, UT results |
| `manifests/runtime_identity.json` | Overlay stamp, donor, file counts, module hashes, versions |
| `manifests/fixture.json` | Selected fixture and candidate accept/reject matrix |
| `manifests/fixture_hashes.txt` | SHA256 of model configs, index, draft weights, main shards |

## G0 — Fixture and MRV2 identity

| Path | Purpose |
|---|---|
| `G0_fixture/fixture_inventory.md` | Fixture table, hashes, reject reasons |
| `G0_mrv2_identity/identity.json` | In-worker MRV2 runner/speculator proof, A0 + B |
| `G0_mrv2_identity/smoke_identity.log` | Initial identity smoke and first bind failure |

## G1 — Capture / operand evidence

| Path | Purpose |
|---|---|
| `G1_capture/README.md` | G1 verdict, observations, root cause |
| `G1_capture/capture_events.json` | 6 CAPTURE + 1 MATERIALIZED recorder events |
| `G1_capture/bind_failure.json` | Exception, traceback, identity at failure |

## G2–G5

| Path | Purpose |
|---|---|
| `G2_refresh/README.md` | G2 = OPEN (blocked by G1) |
| `G3_read_oracle/README.md` | G3 = OPEN; no physical read-set observer |
| `G4_write_oracle/README.md` | G4 = OPEN; no OFF/ON write comparison |
| `G5_timeline/README.md` | G5 = OPEN; no NPU timeline trace |

## Controls and negatives

| Path | Purpose |
|---|---|
| `negative/README.md` | Device controls and CPU matrix summary |
| `negative/A0/result.json`, `driver.log` | Window OFF baseline |
| `negative/A1/result.json`, `driver.log` | Window ON, public gate closed |
| `negative/B/result.json`, `driver.log` | Window + internal flag, runtime failure |
| `negative/B/result_run1.json`, `driver_run1.log` | First reproducible failure |
| `negative/B_dflash/result.json`, `driver.log` | DFlash fixture unavailable |
| `negative/negative_matrix_cpu.json`, `.log` | 31/31 policy/validation checks |

## Commands and requests

| Path | Purpose |
|---|---|
| `commands/build_graph_char_overlay.sh` | Overlay build recipe |
| `commands/env_graph_char.sh` | Runtime env (MRV2, path guard, cache isolation) |
| `commands/sitecustomize.py` | Legacy source blocking |
| `commands/driver_case.py` | Deterministic A0/A1/B driver |
| `commands/smoke_identity.py` | Initial identity smoke |
| `commands/negative_matrix_cpu.py` | CPU policy/validation matrix |
| `commands/probe_import_provenance.py` | Import provenance probe |
| `commands/assemble_evidence.py` | Evidence assembly |
| `commands/argv_*.txt` | Exact environment and argv per case |
| `requests/request_contract.md` | Driver contract |
| `requests/prompt.txt`, `prompt.sha256` | Exact prompt and hash |

## Tools integrity

| Path | Purpose |
|---|---|
| `00_tools/team_tools_before.txt` | Inventory + sha256 before |
| `00_tools/team_tools_after.txt` | Inventory + sha256 after |
| `00_tools/verdict.txt` | `ORIGINAL_TEAM_TOOLS_UNCHANGED` |
| `00_tools/sw_skill_usage.md` | Skill/tool reuse audit |

## Reading order

1. `reports/P7X_Graph_G1_G5_Teacher_Summary_CN.md`
2. `reports/P7X_Graph_G1_G5_NPU_Characterization.md`
3. `G1_capture/README.md`
4. `reports/P7X_Graph_G1_G5_Next_Action.md`
5. `/home/wenqing/reference/P7X_Graph_G1_G5_A3_Characterization_CN.md`
