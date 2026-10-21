# RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report

RUN_ID: `20261019_055109_13373fff`  
Source: `13373fff637e819f3db125e05064f94cba3475a3`  
This mandatory file is generated even though the Base is not PASS.

---

## 1. Gap table

| Gap ID | Gate | Observed fact | Expected | First divergent function | Required local investigation/change | Regression / NPU rerun | Scope | Owner | Confidence | Evidence IDs |
|---|---|---|---|---|---|---|---|---|---|---|
| GAP-001 | B capture / G1 | `RuntimeError: capture operand observer is already attached` on second capture descriptor | attach is per-descriptor/per-metadata and idempotent | `attach_parallel_graph_capture_operand_observer` (`draft_window_graph_characterization.py:1006`), called from `dflash/capture.py:376` | Make observer context lifecycle descriptor-scoped and idempotent; do not reuse a stale attribute across capture calls | Add multi-descriptor red test; NPU rerun fixed `[7,14,28]` | production observer code | local Codex | high | EVID-CMD-0019, EVID-B-RESULT, EVID-B-TRACEBACK, EVID-B-ARTIFACT |
| GAP-002 | G1/G2/G4/G5 | fixed-contract capture does not complete | capture/bind/replay/update/consumer/completion for `(1,7),(2,14),(4,28)` | GAP-001 | none beyond GAP-001; rerun fixed contract | NPU fixed `[7,14,28]` with 1/2/4 prompts | device campaign | local + device | high | EVID-B-RESULT |
| GAP-003 | G1 L3 | no ACL task internal binding | task handle/event/stream correlated to persistent Window operand | no device trace | Collect msprof task-level trace; if insufficient, add a local observation seam with explicit fields | NPU trace run after GAP-001 | observability/device tooling | device owner | medium | EVID-NO-TRACE |
| GAP-004 | G3 L5 | no physical read set | physical block/token read set equals oracle | no device trace | Use msprof Memory/MemoryAccess or equivalent; correlate with FIA operator | NPU trace after GAP-001 | device tooling | device owner | medium | EVID-NO-TRACE, EVID-G3-ORACLE |
| GAP-005 | G5 L6 | no effective update generation/completion | UPDATE(N) target and safe reuse proven | no device timeline | Collect replay/update/consumer/completion trace; source already says NPU timeline is required | NPU trace after GAP-001 | device tooling/observability | device owner | high | EVID-NO-TRACE |
| GAP-006 | G4 Target numeric | no Target logits/output | aligned OFF/ON Target numeric comparison | driver not collecting | Add driver seam for Target logits/output; freeze tolerance before run | host + NPU rerun | driver | local/device | medium | EVID-A0-RESULT, EVID-B-RESULT |
| GAP-007 | G2 NPU A/B/A′ | host A/B/A′ only | device same-backing A/A′ content, B different, new generation/epoch | no device run | After GAP-001, drive real request lifecycle; if allocator prevents natural A/A′, add test-only fixture seam, do not fake live table | NPU A/B/A′ | driver/test fixture | local/device | medium | EVID-HOST-LIFECYCLE |
| GAP-008 | G5 abort | host abort/exception only | device lease/pending consumer/backing behavior | no device run | Use existing safe cancel interface if present; otherwise record missing seam | NPU abort cases after GAP-001 | driver/device | local/device | medium | EVID-HOST-LIFECYCLE |
| GAP-009 | G1/G3/G5 | msprof not collected | device trace attached to evidence | B blocked before replay | Collect after GAP-001; export tool/version/command/filter/counts | NPU trace run | device tooling | device owner | high | EVID-NO-TRACE |
| GAP-010 | B old fix point | old alias failure not reached | device verification of canonical-sharing fix | capture attach | Depends on GAP-001; rerun fixed contract and inspect `bind_read_carrier` outcome | NPU rerun fixed contract | device campaign | local/device | high | EVID-B-RESULT, EVID-HOST-REAL-OWNER |

---

## 2. GAP-001 detail (the only proven code defect)

### 2.1 Exact code path

```text
DFlashAclGraphManager.capture
  -> DFlashCudaGraphManager.create_forward_fn(desc, warmup=True/False)
  -> ascend_prepare_dflash_inputs_to_capture
  -> record_parallel_graph_capture(...)
  -> attach_parallel_graph_capture_operand_observer(provider, identity, metadata)
```

`attach_parallel_graph_capture_operand_observer` iterates all layer metadata and does:

```python
if hasattr(layer_metadata, _CAPTURE_OPERAND_CONTEXT_ATTRIBUTE):
    raise RuntimeError("capture operand observer is already attached")
setattr(layer_metadata, _CAPTURE_OPERAND_CONTEXT_ATTRIBUTE, context)
```

### 2.2 Why it fails on device

The capture manager calls the helper for multiple descriptors and for warmup/capture.
The attention metadata builder can reuse layer metadata objects. The attribute set
by the first attach remains on the object; the next attach raises.

The host UT uses a fake builder that returns fresh metadata objects, so it does not
exercise this lifecycle.

### 2.3 Minimal local change

Choose one:

- Store the capture context in a descriptor-scoped map keyed by metadata object
  identity, and overwrite/refresh it instead of raising; or
- Attach once per metadata object and make the attach idempotent if the context
  belongs to the same provider/identity; or
- Clear the attribute when the capture scope for a descriptor ends.

Do not change the operator operand semantics: the context must still identify the
exact capture descriptor/identity and must not be shared across descriptors.

### 2.4 Red test

Add a host test that:

- builds multiple capture descriptors (`(4,28)`, `(2,14)`, `(1,7)`);
- reuses the same layer metadata objects across descriptor/warmup/capture calls;
- asserts no duplicate-attach error;
- asserts each recorded `capture_operator` event carries the correct descriptor
  and persistent backing address.

Suggested name:

```text
test_capture_operand_observer_is_idempotent_across_descriptors
```

### 2.5 Invariants that must not break

- Only explicit Draft metadata receives the observer.
- The observer is not attached to Target metadata.
- Capture/update operand checks still require the registered Window backing and lengths.
- Public Graph Window gate remains fail-closed.

### 2.6 Next minimal NPU rerun

1. fixed `[7,14,28]`, 1 prompt → `(1,7)` capture/bind/replay.
2. fixed `[7,14,28]`, 2 prompts → `(2,14)`.
3. fixed `[7,14,28]`, 4 prompts → `(4,28)`.
4. A0/A1 controls unchanged.
5. G2 A/B/A′ in one session.
6. G3 short/boundary/non-boundary/long.
7. G4 OFF/ON.
8. G5 trace.

---

## 3. What cannot be inherited from the old SHA

- Device capture/bind/replay evidence from `8cb4bed6`: the old device run failed at
  bind; `13373fff` changes the metadata build/validation path. Old evidence cannot
  be reused.
- Host regression passing on `13373fff` does not establish device L2/L3/L5/L6.
- A0/A1 from this run are valid only for this exact SHA/tree/runtime overlay.
- Single-size capture diagnostics are not valid Base evidence and cannot be promoted
  to `(1,7)/(2,14)/(4,28)` coverage.

---

## 4. Dependency order

```text
GAP-001 (capture observer)  -> GAP-002 (fixed-contract coverage)
                            -> GAP-010 (old fix point on device)
                            -> GAP-007 (device A/B/A')
                            -> GAP-008 (device abort)

GAP-003/004/005/009 (device trace) can be prepared in parallel but can only be
collected after GAP-001.
GAP-006 (Target numeric) can be developed in parallel on host.
```

---

## 5. Architecture / acceptance questions

No new architecture decision is required for GAP-001; it is an observer lifecycle
defect. Do not use this finding to change the Window planner, Graph manager,
canonical sharing contract, or public gate.

The following remain acceptance-contract questions for the next round:

- Exact required evidence level for G1 L3 (task handle alone vs full operand address).
- Exact device read-set source for G3 L5 (msprof Memory/MemoryAccess vs another tool).
- Exact completion owner definition for G5 L6.
- Whether device A/B/A′ can be produced through a real request lifecycle without a
  test-only allocator seam.
