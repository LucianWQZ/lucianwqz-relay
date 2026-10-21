**# P7X_A3_05_G1_G5_Decisions**


RUN_ID: `20261019_055109_13373fff`

Source: `13373fff637e819f3db125e05064f94cba3475a3`


Evidence-level key:


- L1: source/host identity, storage, generation, descriptor.

- L2: actual FIA capture/task-update call-boundary operand.

- L3: ACL task internal real binding.

- L4: device task/read boundary correlation.

- L5: physical memory transaction/read set.

- L6: effective generation/completion/safe reuse.


Device positive path is blocked at capture; host evidence is explicitly separated.


**---**


**# G1 — Operand Binding Report**


**## G1_HOST_OPERATOR_BOUNDARY**


- Standard and source: actual `npu_fused_infer_attention_score.out` call boundary operands recorded by the production observer; expected persistent Window backing equals capture and update operator table; length operands equal registered Window lengths.

- Scope: fixed contract `[7,14,28]`, DSpark, `(1,7)/(2,14)/(4,28)`.

- Expected: at least one `capture_operator` per captured bucket and one `update_operator` per runtime generation; expected/captured/actual table addresses equal; length values match.

- Actual: partial artifact has ****1**** `capture` event for `(4,28)` and ****0**** `operand_events`. No `capture_operator`, no `update_operator`, no `bound`.

- Evidence level: L1/L2 partial.

- Status: `OPEN`.

- First divergence: `capture operand observer is already attached` at `draft_window_graph_characterization.py:1006`, before the next descriptor's operator boundary.

- Evidence IDs: `EVID-B-ARTIFACT`, `EVID-B-RESULT`, `EVID-CMD-0019`.

- Missing content: capture_operator operand records; update_operator records; bound events; runtime generation.

- Next owner/action: local fix of observer lifecycle; rerun fixed contract.


Observed capture event facts (not a PASS):


| Field | Value |

|---|---|

| descriptor | `mode=FULL;reqs=4;tokens=28;uniform=7` |

| expected/backing table address | 20623361164800 |

| length values | 1151 × 4 |

| slot mapping | -1 × 28 |

| positions | 0 × 28 |

| query layout | [0,7,14,21,28] |

| generation / epoch | null / null |


**## G1_ACTUAL_ACL_TASK_INTERNAL**


- Standard and source: real ACL task internal binding, not Python builder input.

- Scope: same fixed contract.

- Expected: task handle/event/stream correlated to the persistent Window table and length operands.

- Actual: no replay; no ACL task trace collected.

- Evidence level: L3.

- Status: `OPEN`.

- First divergence: capture attach (no task exists yet).

- Evidence IDs: `EVID-NO-TRACE`.

- Missing content: task internal binding; exact device operand address.

- Next owner/action: after capture fix, collect msprof/task trace; correlate handle/event/stream.


**## Old alias fix (host vs device)**


- Host: PASS (`test_real_target_metadata_sharing_is_allowed_for_full_write_carriers`; `test_draft_private_fields_still_reject_target_storage_alias`).

- Device: `NOT_REACHED` — the fixed-contract run fails before bind.

- No device claim is made that the old alias failure is fixed.


**---**


**# G2 — A/B/A′ Report**


**## G2_HOST_A_B_A**


- Standard and source: host UT with same persistent backing, three generations A/B/A′, same address, A/A′ content equal, B different, generation ids different.

- Scope: host synthetic owner/provider.

- Expected: stable address + current content + no one-generation lag.

- Actual: `test_runtime_candidate_host_a_b_a_refreshes_content_at_stable_address` PASS; campaign auditor also PASS.

- Evidence level: L1 host.

- Status: `PASS` (host only).

- First divergence: none on host.

- Evidence IDs: `EVID-HOST-LIFECYCLE`.

- Missing content: device A/B/A′.

- Next owner/action: device A/B/A′ after capture fix.


**## G2_NPU_A_B_A**


- Standard and source: same as above, on device, via real request lifecycle.

- Scope: device fixed contract.

- Expected: three BOUND events with same backing, different current content, new generation/epoch, no previous Window as source.

- Actual: no BOUND event; capture failed.

- Evidence level: L2.

- Status: `NOT_RUN` (blocked by G1 capture).

- First divergence: capture attach.

- Evidence IDs: `EVID-B-RESULT`.

- Missing content: device A/B/A′; request fingerprint; source lineage.

- Next owner/action: local capture fix; then construct real A/B/A′ requests.


**## G2_CANONICAL_SOURCE_LINEAGE**


- Standard and source: each generation's input must come from canonical Full source; previous Window must never become the next source.

- Scope: device.

- Expected: owner/storage/source-stage proof per generation.

- Actual: no device generation; host test covers the recorder behavior only.

- Evidence level: L2.

- Status: `OPEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-B-ARTIFACT`, `EVID-HOST-LIFECYCLE`.

- Missing content: device source lineage.

- Next owner/action: device A/B/A′ + artifact audit.


**---**


**# G3 — Independent Oracle Report**


**## G3_INDEPENDENT_ORACLE**


- Standard and source: `draft_window_graph_oracle.py`, independent of the production planner; inputs are canonical table/length geometry.

- Scope: host synthetic canonical inputs; SHORT/BOUNDARY/NONBOUNDARY/LONG.

- Expected and actual:


| Case | H/E/upper | W | block span | S | visible | required columns | expected block ids | status |

|---|---|---:|---:|---:|---:|---:|---|---|

| SHORT | 80/80/80 | 1024 | 128 | 0 | 80 | 1 | [1] | PASS |

| BOUNDARY | 1024/1024/1024 | 1024 | 128 | 0 | 1024 | 8 | [1..8] | PASS |

| NONBOUNDARY | 1000/1000/1000 | 1024 | 128 | 0 | 1000 | 8 | [1..8] | PASS |

| LONG | 2048/2048/2048 | 1024 | 128 | 1024 | 1024 | 8 | [9..16] | PASS |


- Negative:

  - `SOURCE_SHORTAGE`: expected reject, actual `RuntimeError: Graph oracle source shortage: start=8 required=8 end=16 valid=8`.

  - `NONZERO_OFFSET`: expected reject, actual `NotImplementedError: Graph oracle base route requires a direct-prefix zero offset`.

- Evidence level: L1 host.

- Status: `PASS` (host oracle only).

- First divergence: none.

- Evidence IDs: `EVID-G3-ORACLE`, `EVID-G3-ORACLE-LOG`.

- Missing content: oracle input bound to real device canonical source.

- Next owner/action: after capture fix, feed device G4 canonical rows into the same oracle and compare to operator records.


**## G3_OPERATOR_BOUNDARY**


- Standard and source: compare oracle expected block ids/columns to actual operator table/length.

- Scope: device.

- Expected: actual operator table values and lengths equal oracle.

- Actual: only one capture event; no `capture_operator` or `update_operator` record.

- Evidence level: L2.

- Status: `OPEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-B-ARTIFACT`.

- Missing content: operator operand records.

- Next owner/action: local capture fix; rerun.


**## G3_TASK_CORRELATION**


- Standard and source: operator operand → ACL task → FIA operator correlation.

- Scope: device.

- Expected: task handle/stream/event correlation.

- Actual: no device trace.

- Evidence level: L3.

- Status: `OPEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-NO-TRACE`.

- Missing content: task trace.

- Next owner/action: msprof task trace.


**## G3_PHYSICAL_MEMORY_TRANSACTION**


- Standard and source: physical read set / memory transaction.

- Scope: device.

- Expected: actual physical block/token read set.

- Actual: not observed.

- Evidence level: L5.

- Status: `OPEN`, `proof_state=UNPROVEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-NO-TRACE`.

- Missing content: msprof Memory/MemoryAccess or equivalent device trace.

- Next owner/action: device tooling experiment; do not downgrade to output correctness.


**---**


**# G4 — OFF/ON Write/Target Report**


**## G4_HOST_WRITE_TARGET_RECORD**


- Standard and source: host `record_g4` construction, canonical sharing accepted, private read isolated.

- Scope: host UT.

- Expected: G4 record contains canonical table, window table, slot/positions/query, target metadata identities, target lengths.

- Actual: `test_runtime_update_operand_and_g4_records_are_machine_readable` PASS; `test_real_target_metadata_sharing_is_allowed_for_full_write_carriers` PASS.

- Evidence level: L1 host.

- Status: `PASS` (host only).

- First divergence: none.

- Evidence IDs: `EVID-HOST-LIFECYCLE`.

- Missing content: device OFF/ON.

- Next owner/action: device OFF/ON after capture fix.


**## G4_FULL_WRITE_TARGET**


- Standard and source: OFF vs ON, same logical step, canonical Full table / slot / positions / query / target metadata / target lengths / KV write / Target numeric.

- Scope: device.

- Expected: no write-side or Target-private mutation; legitimate canonical sharing accepted.

- Actual:

  - A0: OK, no characterization, no G4 record (by design).

  - A1: early GRAPH_FROZEN, no G4 record.

  - B: capture partial, no G4 record.

- Evidence level: L2.

- Status: `OPEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-A0-RESULT`, `EVID-A1-RESULT`, `EVID-B-ARTIFACT`.

- Missing content: device G4 record; OFF/ON comparison; Target numeric.

- Next owner/action: local capture fix; device OFF/ON with process-scoped comparison rules.


**## G4_DEVICE_KV_WRITE**


- Standard and source: actual KV physical write transaction.

- Scope: device.

- Expected: physical write evidence beyond slot values.

- Actual: not observed.

- Evidence level: L5.

- Status: `OPEN`, `proof_state=UNPROVEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-NO-TRACE`.

- Missing content: msprof memory/write trace.

- Next owner/action: device tooling.


**## G4_TARGET_NUMERIC**


- Standard and source: Target logits/output under aligned token/position/mask/KV conditions.

- Scope: device.

- Expected: real Target numeric with pre-frozen tolerance.

- Actual: not collected.

- Evidence level: L1/L2.

- Status: `NOT_RUN`.

- First divergence: capture attach.

- Evidence IDs: none.

- Missing content: Target logits/output; tolerance source.

- Next owner/action: driver seam to capture Target numeric; rerun.


**---**


**# G5 — Replay/Update/Completion Timeline**


**## G5_EVENT_INSTRUMENTATION**


- Standard and source: host recorder produces replay_submitted, update_event_recorded, proposal_retired with real event identity and no host synchronize.

- Scope: host UT.

- Expected: ordered lifecycle events; event_complete queried without sync; proposal retired is not device completion.

- Actual: `test_replay_submission_records_real_event_without_synchronizing` PASS; `test_campaign_auditor_requires_all_evidence_layers_and_detects_host_a_b_a` PASS; `test_runtime_candidate_recorder_exception_releases_bound_carrier` PASS.

- Evidence level: L1 host.

- Status: `PASS` (host only).

- First divergence: none.

- Evidence IDs: `EVID-HOST-LIFECYCLE`.

- Missing content: device timeline.


**## Observed device timeline**


```

capture (4,28)  ->  capture observer re-attach failure

```


No materialized/bound/live/replay/consumer/update for the fixed-contract Graph attempt. The eager-only diagnostics (cap7/14/28) produced materialized/proposal_retired but did not use Graph and are not G5 evidence.


**## G5_FIRST_REPLAY_SOURCE**


- Standard and source: first replay content generation.

- Expected: CURRENT / PREVIOUS / CAPTURE_DUMMY / UNRESOLVED.

- Actual: no replay.

- Evidence level: L2.

- Status: `NOT_RUN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-B-RESULT`.

- Missing content: replay event + operand generation.

- Next owner/action: rerun after capture fix.


**## G5_UPDATE_EFFECTIVE_GENERATION**


- Standard and source: UPDATE(N) actual effect on replay N/N+1; requires NPU timeline.

- Expected: CURRENT / NEXT / OTHER_PROVEN / UNRESOLVED.

- Actual: `UNRESOLVED`; no update event.

- Source fact: `draft_window_graph.py` `assert_update_effective_for` explicitly raises `effective graph update generation requires NPU timeline evidence`.

- Evidence level: L3.

- Status: `OPEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-NO-TRACE`.

- Missing content: NPU task trace.

- Next owner/action: device trace.


**## G5_COMPLETION_REUSE**


- Standard and source: device completion owner and earliest safe carrier reuse.

- Expected: completion/retire/reuse ordering with correct consumer and stream dependency.

- Actual: no device completion; no retire in the Graph attempt.

- Evidence level: L6.

- Status: `OPEN`.

- First divergence: capture attach.

- Evidence IDs: `EVID-NO-TRACE`.

- Missing content: completion/stream/event evidence.

- Next owner/action: device trace + device abort/reuse cases.


**## G5_ABORT_EXCEPTION**


- Standard and source: materialize/bind/submit/abort/reuse state machine.

- Scope: host + device.

- Expected: buffered failure cases release lease/carrier; stale identity rejected; pending reader not overwritten.

- Actual: host `test_runtime_candidate_recorder_exception_releases_bound_carrier` PASS; device abort not run.

- Evidence level: L1 host.

- Status: `HOST_PASS_DEVICE_OPEN`.

- First divergence: capture attach for device.

- Evidence IDs: `EVID-HOST-LIFECYCLE`.

- Missing content: device abort/exception lifecycle.

- Next owner/action: after capture fix, use existing safe cancel interface if available; otherwise record missing seam.


**---**


**# Negative Matrix**


- CPU: 31/31 MATCH (`negative/negative_matrix_cpu.json`).

- Device: A0 CONFIG_OFF PASS; A1 flag OFF `GRAPH_FROZEN` PASS; B fixed contract new capture failure.

- Other device negatives not run because the positive capture path is blocked.

- Host-covered negatives are labeled L1 host, not device.


**# Cross-Artifact Audit**


- Repository audit on partial B artifact: `ready_for_device_campaign=false`; G1 host OPEN; physical/effective-generation require device trace.

- Independent checker first run: 26 checks, 25 PASS, 1 OPEN (deliverables not yet written), 0 FAIL.

- The checker validates evidence consistency only; it does not convert host data into device proof.
