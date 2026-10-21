**# P7X_A3_08_Failures_And_Limits**


RUN_ID: `20261019_055109_13373fff`

This document lists every failure, OPEN item, tool limitation and uncovered case.

It separates proven production defects from driver/observability/tool gaps.


**---**


**## FIND-001 — capture operand observer is not idempotent across capture descriptors**


| Field | Value |

|---|---|

| Classification | `PRODUCTION_DEFECT` |

| Severity | critical / blocking |

| Gate | B capture → G1 host operator |

| Case/attempt/command | `B`, attempt 1, `CMD-0019` |

| Expected | each capture descriptor attaches its own observer context; fixed `[7,14,28]` completes capture |

| Observed | `RuntimeError: capture operand observer is already attached` |

| First divergent stage | DFlash startup capture, second descriptor's `create_forward_fn(desc, warmup=True)` |

| First divergent function | `attach_parallel_graph_capture_operand_observer` at `draft_window_graph_characterization.py:1006`, called from `dflash/capture.py:376` |

| Evidence IDs | `EVID-CMD-0019`, `EVID-B-RESULT`, `EVID-B-TRACEBACK`, `EVID-B-ARTIFACT` |

| Proven facts | first descriptor `(4,28)` recorded one capture event; the next attach found the context attribute already present on a layer metadata object |

| Unproven | whether the attribute is reused across descriptors, across warmup/capture, or both; exact object identity chain |

| Observer impact | blocks all fixed-contract Graph capture; no replay/update/completion exists |

| What clears it | local fix + red test + device rerun |

| Blocks Base | yes |

| Blocks local fix | is the local fix |

| Owner | local Codex |

| Confidence | high (traceback + source + partial artifact) |


Minimal repro: fixed `[7,14,28]`, flag 1, DSpark, W1024, device 5; capture reaches `capture.py:376` and raises.


**---**


**## FIND-002 — old alias fix not reached on device**


| Field | Value |

|---|---|

| Classification | `OBSERVABILITY_GAP` / evidence gap |

| Severity | high |

| Gate | B old fix point |

| Case/attempt/command | `B`, attempt 1, `CMD-0019` |

| Expected | bind/publish after capture, to test canonical-sharing acceptance |

| Observed | capture failed earlier; bind never executed |

| First divergent stage | capture observer attach |

| Evidence IDs | `EVID-B-RESULT`, `EVID-HOST-REAL-OWNER` |

| Proven facts | host regression tests pass; device old failure is not reproduced and not verified |

| Unproven | device behavior of the fixed isolation/write-carrier split |

| Blocks Base | yes (indirectly) |

| Owner | local Codex (after FIND-001) |


**---**


**## FIND-003 — G1 L3 ACL task internal binding is not observable from Python**


| Field | Value |

|---|---|

| Classification | `OBSERVABILITY_GAP` |

| Severity | high |

| Gate | G1_ACTUAL_ACL_TASK_INTERNAL |

| Expected | real ACL task internal operand binding |

| Observed | only Python call-boundary records exist in the candidate; no task-internal trace |

| First divergent stage | no replay (capture blocked) |

| Evidence IDs | `EVID-NO-TRACE` |

| Proven facts | candidate marks operand events as `HOST_OPERATOR_BOUNDARY_FACT`; repo audit marks L3 `DEVICE_TRACE_REQUIRED` |

| Unproven | actual task operand address |

| What clears it | msprof/task trace correlated with handle/event/stream |

| Blocks Base | yes, for G1 L3 |

| Owner | device tooling + local seam if needed |


**---**


**## FIND-004 — G3 physical read set is not observable**


| Field | Value |

|---|---|

| Classification | `DEVICE_TOOL_LIMITATION` |

| Severity | high |

| Gate | G3_PHYSICAL_MEMORY_TRANSACTION |

| Expected | physical block/token read set |

| Observed | not collected; no device replay due to FIND-001 |

| Evidence IDs | `EVID-NO-TRACE` |

| Proven facts | `msprof` exists (CANN 9.1.0, msprof 26.1.0) and supports task/memory metrics, but no trace was collected |

| Unproven | physical read set |

| What clears it | msprof Memory/MemoryAccess or equivalent device trace plus operator correlation |

| Blocks Base | yes, for G3 L5 |

| Owner | device tooling |


**---**


**## FIND-005 — G5 effective update generation / completion requires NPU timeline**


| Field | Value |

|---|---|

| Classification | `OBSERVABILITY_GAP` |

| Severity | high |

| Gate | G5_UPDATE_EFFECTIVE_GENERATION / G5_COMPLETION_REUSE |

| Expected | prove UPDATE(N) affects current/next replay; prove completion owner and safe reuse |

| Observed | no device replay/update; no timeline |

| Source fact | `draft_window_graph.py` `assert_update_effective_for` raises `effective graph update generation requires NPU timeline evidence` |

| Evidence IDs | `EVID-NO-TRACE` |

| Proven facts | candidate itself declares this needs device timeline |

| Unproven | effective generation mapping; completion owner; earliest safe reuse |

| What clears it | NPU trace covering replay/update/consumer/completion |

| Blocks Base | yes, for G5 |

| Owner | device tooling |


**---**


**## FIND-006 — Target numeric comparison not collected**


| Field | Value |

|---|---|

| Classification | `SERVER_DRIVER_GAP` |

| Severity | medium |

| Gate | G4_TARGET_NUMERIC |

| Expected | real Target logits/output under aligned conditions |

| Observed | not collected; B blocked before runtime |

| Evidence IDs | `EVID-A0-RESULT`, `EVID-B-RESULT` |

| Proven facts | A0 output tokens are deterministic and match the old contract; they are not Target logits |

| Unproven | OFF/ON Target numeric equivalence |

| What clears it | driver seam for Target logits/output; rerun |

| Blocks Base | yes, for the G4 numeric subgate |

| Owner | driver + device |


**---**


**## FIND-007 — device A/B/A′ request lifecycle not constructed**


| Field | Value |

|---|---|

| Classification | `SERVER_DRIVER_GAP` |

| Severity | medium |

| Gate | G2_NPU_A_B_A |

| Expected | same persistent backing across three generations, A/A′ same content, B different |

| Observed | host A/B/A′ PASS; device A/B/A′ not run |

| Evidence IDs | `EVID-HOST-LIFECYCLE`, `EVID-B-RESULT` |

| Proven facts | host recorder can do it |

| Unproven | device allocator/request lifecycle can naturally produce the required A/A′ content |

| What clears it | after capture fix, drive real request lifecycle; if allocator cannot produce it naturally, record a test-only fixture seam |

| Blocks Base | yes, for G2 device |

| Owner | driver/device |


**---**


**## FIND-008 — device abort/exception lifecycle not run**


| Field | Value |

|---|---|

| Classification | `SERVER_DRIVER_GAP` |

| Severity | medium |

| Gate | G5_ABORT_EXCEPTION |

| Expected | materialize/bind/submit/abort/reuse behavior on device |

| Observed | host recorder exception test PASS; device abort not run |

| Evidence IDs | `EVID-HOST-LIFECYCLE` |

| Proven facts | host state machine releases bound carrier on recorder exception |

| Unproven | device lease/pending consumer/backing behavior |

| What clears it | existing safe cancel interface + device abort cases |

| Blocks Base | yes, for the device abort subgate |

| Owner | driver/device |


**---**


**## FIND-009 — single-size capture diagnostics fall back to eager or fail install**


| Field | Value |

|---|---|

| Classification | `ACCEPTANCE_CONTRACT_QUESTION` / diagnostic note |

| Severity | low |

| Gate | diagnostics only |

| Observed | `[7]/[14]/[28]` produce target manager `needs_capture=false`; `[24]` produces draft manager with no descriptors |

| Evidence IDs | `EVID-DIAG` |

| Proven facts | target manager capture gating controls whether the draft manager is ever invoked |

| Unproven | none claimed |

| Note | these runs are not fixed-contract evidence and must not be counted as Graph coverage |


**---**


**## FIND-010 — A1 zero-state proof is source/exception-location based**


| Field | Value |

|---|---|

| Classification | `ACCEPTANCE_CONTRACT_QUESTION` (minor) |

| Severity | low |

| Gate | A1 early gate |

| Observed | LLM construction fails before the driver can inspect the speculator; zero-state is proven by the exception location before FullSource/workspace/provider/carrier |

| Evidence IDs | `EVID-A1-RESULT` |

| Proven facts | failure at `require_local_materialization` in `build_draft_window_source_capability` |

| Unproven | object-level zero-state inspection, which is impossible after a failed constructor |

| Note | source path and exception location are sufficient for the early-gate claim; no device positive claim is made |


**---**


**## FIND-011 — msprof/NPU trace not collected**


| Field | Value |

|---|---|

| Classification | `DEVICE_TOOL_LIMITATION` / not attempted |

| Severity | high |

| Gate | G1 L3, G3 L5, G5 L6 |

| Expected | device trace |

| Observed | no trace; fixed-contract B fails before replay |

| Evidence IDs | `EVID-NO-TRACE` |

| Proven facts | `msprof` is installed and advertises task/memory profiling |

| Unproven | all device L3/L5/L6 facts |

| What clears it | collect after capture fix; otherwise record tool limitation |

| Blocks Base | yes |

| Owner | device tooling |


**---**


**## FIND-012 — shared team tool directories**


| Field | Value |

|---|---|

| Classification | integrity note |

| Severity | none |

| Observed | 2296 files before/after; path-keyed SHA256 comparison unchanged |

| Evidence IDs | `EVID-TEAM-TOOLS` |

| Note | shared tool dirs may receive external generated outputs, but this campaign did not write to them |


**---**


**## Global limits**


- No performance conclusion is possible or intended.

- No physical read/write claim is made from outputs or Python pointers.

- No device L3/L5/L6 claim is made from host tests.

- No A1 run is used as a substitute for Window-ON observer-off validation.
