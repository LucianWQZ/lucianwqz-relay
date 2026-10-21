# P7-X Graph G1-G5 Observability Audit

Date: 2026-10-17  
Commit: `13373fff637e819f3db125e05064f94cba3475a3`  
Scope: Base DSpark/DFlash dense-FIA characterization only

## 1. Evidence taxonomy

The implementation uses explicit evidence levels to avoid turning Python
metadata observations into device claims.

| Level | Meaning | Available after this repair? |
|---|---|---|
| source/host identity | Python object/storage, generation, descriptor, route | yes |
| operator-call boundary | exact operands passed to Ascend FIA capture/task-update call | yes, labelled `HOST_OPERATOR_BOUNDARY_FACT` |
| ACL task internal binding | address retained inside opaque task/runtime | not exposed by current Python source; device trace required |
| physical memory transaction/read set | blocks actually read by NPU | no; CANN/msprof/msprobe required |
| completion/effective generation | update/replay/event causal relationship | event identities available; NPU task timeline required |

## 2. Source audit

### `vllm_ascend.compilation.acl_graph`

`update_full_graph_params()` resolves the actual attention implementation and
calls its `update_graph_params()`. The typed characterization binding is passed
only after existing backend attribution succeeds. Ordinary callers retain the
pre-repair call shape.

### `AscendAttentionBackendImpl`

`full_graph_fia()` constructs the exact `attn_params` captured for the FIA
operator, invokes `npu_fused_infer_attention_score.out`, obtains the graph task
group handle, and now records the actual block-table/length operands at that
boundary when the metadata carries an explicit characterization context.

`update_graph_params()` substitutes Draft metadata table/lengths, invokes the
same FIA out operator inside task update, ends update, records the existing
ExternalEvent, and now records the actual substituted operands.

### ACL task object limitation

The `_NPUTaskGroupHandle` and current torch_npu Python APIs used by this code do
not expose an introspectable list of retained operand addresses. Therefore the
new records are the strongest source-level/operator-boundary facts, not proof
of the runtime's internal descriptor or physical memory reads.

## 3. G1 — captured/rebound operand address

### Locally prepared

- expected persistent backing address from `DraftWindowGraphCaptureIdentity`;
- actual capture FIA call table address;
- captured length operand kind/address/values;
- actual task-update FIA table address;
- captured-vs-updated table address;
- backend/consumer/layer/descriptor;
- handle, event and stream identity;
- runtime generation and mapping epoch at update.

### Next A3 PASS requirement

The artifact must contain both `capture_operator` and `update_operator` records,
with table addresses equal to the expected persistent backing for the selected
descriptor. A CANN/task trace should correlate the handle/operator with the
same address if the tooling exposes it.

### Current verdict

```text
G1 OBSERVABILITY PREPARATION: READY
G1 DEVICE VERDICT: OPEN
```

## 4. G2 — stable backing A/B/A'

The machine artifact audit recognizes the last three `BOUND` generations and
requires:

```text
same backing address
A content != B content
A' content == A content
A'.generation_id != A.generation_id
```

Existing provider identity checks reject stale A authorization for A'. Unit
tests also retain early-overwrite and stale-generation fail-closed behavior.

```text
G2 HOST PREPARATION: READY
G2 NPU REPLAY RESULT: OPEN
```

## 5. G3 — read-set evidence

### Independent CPU oracle

`draft_window_graph_oracle.py` does not import or call the production Window
planner. Given the full table, `H`, `E`, upper, `W`, legacy alignment, block
span, query width and valid count, it computes:

- aligned `S`;
- `V=E-S`;
- projected upper;
- source start column and offset;
- required columns;
- expected full-table column indices;
- expected block IDs;
- source shortage errors.

Tests cover short, exact boundary, non-boundary, long, future column, nonzero
offset rejection and source shortage.

### Operator-boundary record

The actual FIA capture/update calls record table and length operands. This can
prove that the host/backend submitted the expected read carrier.

### Evidence that still requires device tooling

Neither a Python pointer nor the operator argument proves which KV blocks were
physically fetched. The rerun must use available CANN/msprof/msprobe operator or
task tracing. If memory-transaction visibility is unavailable, the strongest
honest result is:

```text
operator-boundary table/length == independent oracle
+ task/operator trace correlation
```

It must be labelled device-boundary evidence, not physical transaction proof.

```text
G3 OBSERVABILITY: DEVICE_TOOL_REQUIRED
```

## 6. G4 — write/Target invariants

The recorder now emits one structured G4 record per bound generation:

- full table pointer/values;
- Window pointer/values;
- slot pointer/values;
- positions pointer/values;
- query-start pointer/values;
- Target root and layer identities;
- Target table addresses/lengths;
- Draft output hash;
- optional Target output hash.

The server driver must retain A0 OFF records and compare them with B ON. The
record is machine-readable, removing reliance on manual log inspection. The
Target output hash is only present if the external driver supplies the actual
Target result; its absence is not to be rewritten as equality.

```text
G4 OBSERVABILITY PREPARATION: READY
G4 DEVICE VERDICT: OPEN
```

## 7. G5 — replay/update/completion lifetime

### Real primitives found

- `torch.npu.Event` recorded on the current stream after graph replay;
- existing backend `torch.npu.ExternalEvent` recorded after task update;
- actual graph task handle identity;
- update stream identity;
- host proposal retirement and P3 lease state.

No `torch.npu.synchronize()` or global synchronize is added. Event `query()` is
used only as non-blocking evidence where supported.

### What these do not prove

- that Python replay return is device completion;
- whether UPDATE(N) affects replay N or N+1;
- that host proposal retirement is a safe device-reuse point;
- that all kernels stopped reading before backing rewrite;
- NPU stream lifetime under contention.

The NPU campaign must correlate generation, replay event, task handle, update
event, stream and retirement in a device/task timeline.

```text
G5 INSTRUMENTATION: READY
G5 EFFECTIVE GENERATION / COMPLETION: DEVICE_TOOL_REQUIRED
```

## 8. Artifact audit semantics

`tools/p7x_graph_g1_g5.py audit` reports host readiness separately from device
requirements. It can mark the campaign ready to proceed only when capture and
update operator records, source stages, G4 records and lifecycle records exist.
It always leaves these classifications explicit:

```text
G1_ACTUAL_ACL_TASK_INTERNAL = DEVICE_TRACE_REQUIRED
G3_PHYSICAL_MEMORY_TRANSACTION = DEVICE_TOOL_REQUIRED
G5_UPDATE_EFFECTIVE_GENERATION = NPU_TASK_TRACE_REQUIRED
```

## 9. Final observability verdict

| Gate | Local preparation | Remaining evidence |
|---|---|---|
| G1 | READY | real A3 operand/task correlation |
| G2 | READY | A/B/A' replay on A3 |
| G3 | DEVICE_TOOL_REQUIRED | CANN/msprof/msprobe device-boundary/read evidence |
| G4 | READY | OFF/ON machine-record comparison and Target result |
| G5 | DEVICE_TOOL_REQUIRED | device timeline, effective generation, safe lifetime |

The next campaign is ready to run, but no G1-G5 device gate is pre-closed by
this local implementation.
