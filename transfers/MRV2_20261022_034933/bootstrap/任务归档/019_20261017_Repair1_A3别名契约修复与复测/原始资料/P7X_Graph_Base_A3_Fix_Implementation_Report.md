# P7-X Graph Base A3 Fix Implementation Report

Date: 2026-10-17  
Repository: `/Users/wenqingzhang/Desktop/vllm/vllm-ascend`  
Branch: `fix/p7x-graph-base-a3-g1g5`  
Parent: `8cb4bed670f395c257c1233db944395159916009`  
Commit: `13373fff637e819f3db125e05064f94cba3475a3`  
Tree: `739cde3de61e65be7cdbd187baebb6d17da04aee`  
Subject: `fix(spec-decode): repair graph window base device contract`

Pinned vLLM remains exactly:

```text
SHA  84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status clean
```

No push was performed.

## 1. Commit scope

```text
14 files changed, 1737 insertions(+), 52 deletions(-)
```

The large line count is primarily bounded characterization evidence schema and
tests. It does not enable public Graph Window support.

## 2. File map

| File | Change | Purpose |
|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window_graph.py` | Adds `DraftWindowGraphMetadataBuild`; separates read carrier validation from canonical write validation | Fix false Target-alias rejection without relaxing Draft-private isolation |
| `vllm_ascend/worker/v2/spec_decode/draft_window.py` | Optional `isolation_view` on P3 metadata publish | Validate pre-restore private state while storing final metadata; eager default unchanged |
| `vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py` | Owner-faithful metadata build; typed G1/G4/G5 evidence recorder; artifact v2; lifecycle/output records | Repair A3 bind and prepare complete rerun evidence |
| `vllm_ascend/worker/v2/spec_decode/draft_window_graph_oracle.py` | New independent integer/source projection and artifact audit | G3 CPU oracle that does not call production planner |
| `vllm_ascend/worker/v2/spec_decode/dflash/capture.py` | Attaches capture-scoped observer context to actual Draft metadata | Correlates capture identity with real FIA capture boundary |
| `vllm_ascend/attention/attention_v1.py` | Records actual FIA capture and update call operands under explicit characterization context | G1/G3 strongest Python/device-boundary evidence |
| `vllm_ascend/compilation/acl_graph.py` | Threads typed update binding only when present | Reaches real backend update path without changing ordinary call shape |
| `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py` | Records replay event and output hash around existing replay | G4/G5 evidence; ordering preserved |
| `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py` | Records existing retirement when characterization is installed | Lifecycle evidence only; no retirement semantic change |
| `vllm_ascend/envs.py` | Optional artifact path variable | Default-off machine-readable output |
| `tools/p7x_graph_g1_g5.py` | New executable `oracle` and `audit` helper | Server rerun automation; does not enable feature |
| `tests/ut/spec_decode/test_draft_window_graph_characterization.py` | Real-owner regression and operator/lifecycle/artifact tests | Red-to-green A3 reproduction and G1-G5 seam coverage |
| `tests/ut/spec_decode/test_draft_window_graph_carrier.py` | Private-alias negative test | Prevents broad isolation relaxation |
| `tests/ut/spec_decode/test_draft_window_graph_oracle.py` | Boundary/source-shortage/future-column oracle tests | Independent math coverage |

## 3. Repaired metadata flow

```text
P3 DraftMetadataInputs
  -> persistent Graph read carrier
  -> Ascend metadata builder
  -> deep-isolated private view
  -> validate Target-private isolation
  -> shallow copy layer object
  -> restore canonical full slot/positions/query
  -> validate Window read identity
  -> validate canonical full write/query identity
  -> publish final Draft metadata with private validation view
  -> consume in internal characterization path
```

The final metadata carries the P3 Window table/length and canonical full
write/query references from the same generation. Previous Window content is
never used as source.

## 4. G1 capture/update dataflow

### Capture

```text
Ascend DFlash/DSpark capture helper
  -> attach capture identity to Draft metadata instance
  -> AscendAttentionBackendImpl.full_graph_fia
  -> npu_fused_infer_attention_score.out actual call
  -> graph_task_group_end handle
  -> CAPTURE_OPERATOR record
```

The record contains expected persistent backing, actual operator-call table
address, length operand address/values where safely available, backend,
consumer, descriptor, handle, event and stream identity.

### Runtime update

```text
Draft Window carrier batch
  -> build typed update binding
  -> update_full_graph_params
  -> AscendAttentionBackendImpl.update_graph_params
  -> npu_fused_infer_attention_score.out task update
  -> ExternalEvent.record(update_stream)
  -> UPDATE_OPERATOR + UPDATE_EVENT_RECORDED records
```

The binding is accepted only by the exact Ascend FIA implementation already
validated by P6 attribution. Paged-attention and sinks paths reject this base
characterization binding.

## 5. G4 record

Each bound generation records machine-readable:

- canonical full table pointer and rows;
- Window table pointer and rows;
- slot mapping pointer and values;
- positions pointer and values;
- query layout pointer and values;
- Target metadata/root/layer identities;
- Target table addresses and read lengths;
- Draft output hash after replay;
- optional Target output hash when supplied by the campaign driver.

The recorder does not mutate any of these objects.

## 6. G5 record

After `super().run_fullgraph()` returns, characterization records a real
`torch.npu.Event` on the current stream without calling synchronize. The
existing backend `ExternalEvent` is recorded after task update. Host proposal
retirement is recorded separately and explicitly labelled as not proving
device completion.

This supplies correlation tokens for the next NPU trace, but does not claim:

- effective update generation;
- replay completion;
- stream-safe backing reuse;
- performance neutrality.

## 7. Artifact and CLI

Optional output:

```bash
export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=/path/to/g1_g5.json
```

Schema:

```text
mrv2-draft-window-graph-characterization-v2
```

Independent oracle example:

```bash
python tools/p7x_graph_g1_g5.py oracle \
  --full-table 10,11,12,13,14,15 \
  --horizon 80 --exact 79 --upper 80 --window 64 \
  --legacy-block-size 16 --block-span 16 \
  --query-width 7 --valid-block-count 5
```

Artifact audit:

```bash
python tools/p7x_graph_g1_g5.py audit /path/to/g1_g5.json \
  --output /path/to/g1_g5_audit.json
```

The CLI loads the standalone oracle directly, so it works from a source
checkout and avoids the repository's `tools/bisect` shadowing the Python
standard-library module.

## 8. Preserved boundaries

- vLLM unchanged;
- public Graph Window gate still closed;
- experimental flag remains mandatory;
- no TP16, Prefix, Eagle3, DSA, MLA, Async, DSA-CP, SFA, mixed, multi-group or DFlash2 Graph implementation;
- no Target mutation;
- no slot/position/query clone or override;
- no global or ContextVar transport;
- no owner swap;
- no global device synchronize;
- no push.

## 9. Local implementation verdict

```text
ALIAS CONTRACT FIX: IMPLEMENTED
OWNER-FAITHFUL REGRESSION: PASS
PRIVATE ALIAS NEGATIVE: PASS
G1-G5 RERUN INSTRUMENTATION: IMPLEMENTED
DEVICE CLAIMS: NOT YET VERIFIED
PUBLIC GRAPH SUPPORT: STILL FROZEN
```
