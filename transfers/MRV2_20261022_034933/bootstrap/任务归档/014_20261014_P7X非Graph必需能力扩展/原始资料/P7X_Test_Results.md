# P7-X Test Results

## Test-first evidence

| Contract | Parent/red behavior | P7-X green behavior |
|---|---|---|
| async metadata lifetime | new tests raised `AttributeError` because handle had no `bound_metadata` | metadata and nested tensors retained until completion/release |
| uncompressed DSA provider | new tests failed because inventory lacked source-geometry/compression facts | DSA/DSA-CP ratio<=1 source capability builds; ratio>1 rejects pre-FullSource |
| DSA-CP shared metadata | new builder test raised `KeyError: common_ratio_to_sas_metadata` | actual DSA-CP builder receives shared request metadata |
| terminal/mixed phase | P8 behavior bypassed terminal and rejected mixed batch | terminal/decode Window rows and continuing full rows coexist with phase identity |

## Final commands and results

All Python commands used the repository virtualenv and pinned upstream source:

```bash
VLLM_VERSION=0.29.0 \
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
.venv/bin/python -m pytest -q <paths>
```

The exact `<paths>` groups were:

```text
tests/ut/spec_decode/test_draft_window.py
tests/ut/spec_decode/test_draft_window_nongraph.py
tests/ut/spec_decode/test_draft_window_async.py
tests/ut/spec_decode/test_draft_window_eager.py
tests/ut/spec_decode/test_draft_window_eagle3.py
tests/ut/worker/test_attn_utils_v2.py

tests/ut/spec_decode
tests/ut/attention
tests/ut/distributed
tests/ut/_310p
tests/ut/worker/v2 tests/ut/worker/test_block_table.py
tests/ut/worker/test_attn_utils_v2.py tests/ut/worker/test_dcp_manager.py
tests/ut/worker/test_pcp_manager_v2.py
tests/ut/test_compressed_prefix_cache.py
tests/ut/patch/platform/test_prefix_cache_cp_patches.py
tests/ut/models/test_glm5next_kv_cache.py
tests/ut/models/test_glm5next_cache_config.py
tests/ut/core
tests/ut/worker
```

| Scope | Result | Classification |
|---|---|---|
| six targeted P7-X/P1-P4/attn-utils files | `291 passed` | PASS |
| full `tests/ut/spec_decode` | `608 passed, 13 skipped, 7 failed` | NOT PASS: retained host VWN backend-selection environment failure |
| full `tests/ut/attention` | `472 passed, 3 skipped` | PASS |
| full `tests/ut/_310p` | `155 passed, 2 skipped` | PASS |
| worker/v2 + block table + attn utils + DCP/PCP managers | `147 passed` | PASS |
| prefix/cache + GLM cache/config | `74 passed, 1 skipped` | PASS |
| full distributed in sandbox | `571 passed, 1 error` | sandbox socket bind blocked |
| failed distributed socket test outside sandbox | `1 passed` | PASS; confirms sandbox-only error |
| full core | `206 passed, 48 failed` | ENVIRONMENT_BLOCKED: missing `httpx` in mooncake dependency path |
| full worker | `446 passed, 12 failed` | ENVIRONMENT_BLOCKED: missing NPU private-use hooks/device and sandbox log path |

The seven spec-decode failures all stop at upstream selector
`ValueError: Invalid attention backend for None` in VWN model construction and
contain no P7-X frame. This same host limitation was already present at P8; it
is not reported as PASS.

## Static quality

| Check | Result |
|---|---|
| Ruff on all 13 changed files | PASS |
| `ruff format --check` | PASS |
| targeted Mypy on 7 production modules | PASS |
| compileall spec_decode + attn_utils | PASS |
| `git diff --check` | PASS |
| local Python repo hooks: package init, logger, forbidden imports, boolean context manager, long functions, symbolic meta | PASS |
| full pre-commit | ENVIRONMENT_BLOCKED while installing actionlint; interrupted after no progress |
| gitleaks hook | ENVIRONMENT_BLOCKED: no `gitleaks` and no `wget` on host |

The binary-safe full diff was checked and applied in a detached temporary
worktree at the exact parent. After staging the applied result,
`git write-tree` produced `71800e2e250f0b4dc51aede643eebff55e39b404`,
exactly matching the implementation commit tree.

No test result in this ledger is NPU evidence.

## Independent-review fix evidence

Final review-fix commit:
`c1c2129aa49ee1de381130729de73124a6ec893a`; final tree:
`384af8a0466f6aea2e73d6217f9802415b5ccd40`.

### Test-first red evidence

The new regression selection was run after adding tests and before production
changes. Seven tests failed as intended: four because
`acquire_with_backpressure` did not exist, one because the live third proposal
still raised pool pressure, one because too-small capacity was not rejected at
initialization, and one because DSA-CP used no effective-authority seam.

After production changes, the same affected set plus all P7-X targeted files
passed.

### Final review-fix commands and results

All commands used `VLLM_VERSION=0.29.0`, pinned vLLM through
`PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm`, and `.venv/bin/python`.

| Scope | Final result | Classification |
|---|---|---|
| six P7-X targeted files | `301 passed` | PASS |
| five directly affected files | `270 passed` | PASS |
| full `tests/ut/spec_decode` | `618 passed, 13 skipped, 7 failed` | NOT PASS: same host VWN backend-selection limitation; zero review-fix frames |
| full `tests/ut/attention` | `472 passed, 3 skipped` | PASS |
| full `tests/ut/_310p` | `155 passed, 2 skipped` | PASS |
| worker/v2 + BlockTables + attn/DCP/PCP utilities | `147 passed` | PASS |
| prefix/cache + GLM cache/config | `74 passed, 1 skipped` | PASS |
| full distributed in sandbox | `571 passed, 1 error` | sandbox localhost bind denied |
| failing distributed test outside sandbox | `1 passed` | PASS; confirms sandbox-only error |
| Ruff + format check on all 9 changed files | PASS | PASS |
| targeted mypy on 4 production files with pinned vLLM import path | PASS | `Success: no issues found in 4 source files` |
| compileall | PASS | PASS |
| `git diff --check` | PASS | PASS |
| local Python repository hooks | PASS | init/logger/import/context-manager/long-function/symbolic-meta |

An initial mypy invocation without the pinned vLLM search path expanded into
unrelated repository dependency errors and was interrupted; it is not recorded
as a successful check. The corrected targeted invocation above is authoritative.

Host fake completion tokens establish control-flow safety only. NPU event,
stream, late-reader, communication, pressure-performance, and lifetime evidence
remain open for the second-round Node101 campaign.
