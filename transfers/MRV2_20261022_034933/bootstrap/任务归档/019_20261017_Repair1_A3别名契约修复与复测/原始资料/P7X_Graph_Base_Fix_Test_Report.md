# P7-X Graph Base A3 Fix Test Report

Date: 2026-10-17  
Commit under test: `13373fff637e819f3db125e05064f94cba3475a3`  
Tree: `739cde3de61e65be7cdbd187baebb6d17da04aee`  
Host: macOS CPU/static environment; no Ascend NPU

All pytest commands used:

```bash
VLLM_VERSION=0.29.0
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm
```

## 1. Red-to-green evidence

### Pre-fix RED

Test added first:

```text
test_real_target_metadata_sharing_is_allowed_for_full_write_carriers
```

On parent `8cb4bed...` behavior it failed with:

```text
ValueError: Draft metadata mutable storage aliases Target metadata
```

This reproduced the first A3 bind failure with real canonical Target/write
ownership.

### Post-fix GREEN

The test passes and asserts:

- slot, positions and query-start retain canonical storage identity;
- Window table and exact length retain private carrier identity;
- Window table/length do not alias Target read storage.

## 2. Targeted repair and observability suite

Command:

```bash
.venv/bin/pytest -q \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py \
  tests/ut/spec_decode/test_draft_window_graph_characterization.py \
  tests/ut/spec_decode/test_draft_window_graph_oracle.py
```

Result:

```text
79 passed
```

Includes:

- real-owner legal sharing;
- private alias hard failure;
- real FIA capture-call operand record;
- real FIA update-call operand record;
- JSON artifact schema/evidence labels;
- replay event without synchronize;
- G4 machine record/output hash;
- host A/B/A audit;
- independent G3 oracle boundaries and failure paths.

## 3. Broad P1-P7X regression

Command covered the final versions of:

- autoregressive Draft metadata;
- DFlash2 proposer and V2 contracts;
- P1 math/policy;
- P3 runtime/async;
- P4 eager/Eagle3;
- P5/P6 Graph binding/carrier;
- P7 eager capability/non-Graph;
- DSpark Graph/proposer/speculator;
- the new characterization/oracle tests.

Exact result:

```text
520 passed
```

## 4. Attention, attn_utils and BlockTables

Command:

```bash
.venv/bin/pytest -q \
  tests/ut/attention/test_attention_v1.py \
  tests/ut/worker/test_attn_utils_v2.py \
  tests/ut/worker/test_block_table.py \
  tests/ut/worker/v2/test_v2_block_table.py
```

Result:

```text
101 passed, 23 subtests passed
```

## 5. Full locally runnable spec_decode

Command:

```bash
.venv/bin/pytest -q tests/ut/spec_decode
```

Result:

```text
668 passed, 13 skipped, 7 failed, 2 subtests passed
```

This command is **not** recorded as PASS. All seven failures are the pre-existing
VWN host-platform failures in:

```text
tests/ut/spec_decode/test_speculators_vwn_eagle3.py
```

Every stack terminates at pinned upstream:

```text
vllm/v1/attention/selector.py:208
ValueError: Invalid attention backend for None
```

No failure stack passes through a file changed by this repair. Classification:

```text
ENVIRONMENT_BLOCKED (host has no valid Ascend attention backend)
```

## 6. Static checks

| Check | Result | Notes |
|---|---|---|
| Ruff changed-file lint | PASS | all 14 changed files |
| Ruff format check | PASS | all 14 changed files |
| targeted mypy | PASS | 5 source modules; pinned vLLM on PYTHONPATH; `--follow-imports=skip --ignore-missing-imports` |
| compileall | PASS | spec_decode, attention_v1, acl_graph and campaign tool |
| `git diff --check` | PASS | no whitespace errors |
| direct CLI oracle smoke | PASS | source checkout invocation produced expected columns `[1,2,3,4]`, IDs `[11,12,13,14]`, `S=16`, `V=63`, upper `64` |

Targeted mypy command:

```bash
.venv/bin/mypy --follow-imports=skip --ignore-missing-imports \
  vllm_ascend/worker/v2/spec_decode/draft_window_graph.py \
  vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py \
  vllm_ascend/worker/v2/spec_decode/draft_window_graph_oracle.py \
  vllm_ascend/worker/v2/spec_decode/dflash/capture.py \
  vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py
```

Result: `Success: no issues found in 5 source files`.

## 7. Repository hooks

`pre-commit run --all-files` was attempted twice:

1. default cache: sandbox could not write `~/.cache/pre-commit/.lock`;
2. writable temporary cache with network approval: hook repositories began
   installing, but actionlint's Go environment timed out downloading pinned
   modules from `proxy.golang.org`.

Representative terminal error:

```text
go install ./...
Get https://proxy.golang.org/...: i/o timeout
```

Classification:

```text
PRE-COMMIT: ENVIRONMENT_BLOCKED
```

Ruff, format, compileall, targeted mypy and diff-check were run independently
and passed. The blocked hook is not reported as PASS.

## 8. Repository boundary audit

### vLLM

```text
HEAD 84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status clean
diff empty
```

### vLLM-Ascend

```text
branch fix/p7x-graph-base-a3-g1g5
HEAD 13373fff637e819f3db125e05064f94cba3475a3
tree 739cde3de61e65be7cdbd187baebb6d17da04aee
status clean
```

No push was performed.

## 9. Evidence limits

These local tests prove Python/state/ownership/operator-call contracts. They do
not prove:

- actual A3 ACL task-internal operand binding;
- physical NPU KV read transactions;
- replay/update effective generation;
- stream completion or safe device reuse;
- NPU outputs or performance.

## 10. Final test verdict

```text
REAL-OWNER REGRESSION: PASS
PRIVATE-ALIAS NEGATIVE: PASS
TARGETED GRAPH/ORACLE: 79 PASS
BROAD P1-P7X: 520 PASS
ATTENTION/ATTN_UTILS/BLOCKTABLES: 101 PASS + 23 SUBTESTS
FULL SPEC_DECODE: 668 PASS / 13 SKIP / 7 ENVIRONMENT-BLOCKED FAILURES
STATIC CHECKS: PASS
PRE-COMMIT: ENVIRONMENT_BLOCKED
NPU: NOT RUN
```
