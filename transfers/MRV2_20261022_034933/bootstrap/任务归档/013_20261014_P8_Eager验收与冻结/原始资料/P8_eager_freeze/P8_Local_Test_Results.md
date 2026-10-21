# P8-E Local Test Results

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

## 1. Exact source under test

| Repository | HEAD | Tree | Working tree |
|---|---|---|---|
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | clean |
| vLLM-Ascend | `4753742ab181920292c504a79eedecf9b428ae1b` | `b7e525c3c9d45617ad1023ad45c6948c466a3631` | clean |

`VLLM_VERSION=0.29.0` was used where the local source checkout requires the
version override. No server debug commit, private vLLM patch, P8 source change, or
Graph provider installation was present.

## 2. Test results

| Test group / command scope | Result | Classification / limitation |
|---|---:|---|
| Exact nine-file P1–P7 targeted Draft Window, P5/P6 graph-host, DFlash2 command listed below | `360 passed, 1 warning` | PASS; Graph tests are host contracts, not Graph runtime evidence. |
| `pytest -q tests/ut/spec_decode` | `588 passed, 13 skipped, 7 failed, 2 subtests passed` | **NOT a full PASS.** Seven retained VWN host-backend failures terminate in upstream `vllm/v1/attention/selector.py:208` with `Invalid attention backend for None`; no P7/Window source appears in those stacks. |
| `pytest -q tests/ut/attention` | `472 passed, 3 skipped, 24 subtests passed` | PASS. |
| `pytest -q tests/ut/distributed` in normal sandbox | `571 passed, 1 error` | Local socket bind denied by sandbox. |
| Same distributed suite outside socket-restricted sandbox | `572 passed, 284 subtests passed` | PASS; resolves the preceding infrastructure error. |
| `pytest -q tests/ut/worker/v2` | `31 passed, 18 subtests passed` | PASS. |
| Relevant BlockTables suites | `14 passed, 21 subtests passed` | PASS. |
| `test_attn_utils_v2.py` + `test_attention_v1.py` | `86 passed, 2 subtests passed` | PASS. |
| `tests/ut/_310p/test_model_runner_v2_310p.py` | `41 passed` | PASS; COMPATIBILITY-family regression remains fail closed. |
| Relevant device/config/speculative-patch/profiling tests | `32 passed` | PASS. |
| Full `tests/ut/test_ascend_config.py` attempt | `51 passed, 71 failed, 13 subtests passed` | **Environment-blocked, not PASS.** Seventy failures require a detectable Ascend platform and one requires generated `vllm_ascend._build_info`. P7 changes none of these files. The earlier `83 passed` figure conflated this file with a separate 32-test config/device group and is superseded. |

Exact targeted command (rerun during final review adjudication):

```bash
env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window.py \
  tests/ut/spec_decode/test_draft_window_runtime.py \
  tests/ut/spec_decode/test_draft_window_eager.py \
  tests/ut/spec_decode/test_draft_window_eagle3.py \
  tests/ut/spec_decode/test_draft_window_graph_binding.py \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py \
  tests/ut/spec_decode/test_draft_window_async.py \
  tests/ut/spec_decode/test_draft_window_eager_capability.py \
  tests/ut/spec_decode/test_dflash2_v2.py
```

The known VWN and config-environment results are retained as limitations. Historical
classification was rechecked; it was not automatically copied into this report.

## 3. Static checks

| Check | Result | Scope / limitation |
|---|---|---|
| Ruff check | PASS | All 28 Python files in the base-to-final delivery range. |
| Ruff format check | PASS | `28 files already formatted` for the complete base-to-final Python path set. |
| Targeted Mypy | PASS | `draft_window.py`, `draft_window_async.py`, `draft_window_eager_capability.py`; follow-imports skipped to avoid platform-only dependency expansion. |
| `compileall` | PASS | Draft Window modules plus touched attention/worker paths. |
| `git diff --check` | PASS | Exact base-to-final delivery range / clean tree. |
| Locally executable pre-commit hooks | PASS | ruff-check, ruff-format, codespell, typos, filename/init/logger/import/boolean-context/long-function/symbolic-meta checks. |
| Network/tool-dependent aggregate hooks | NOT RUN | actionlint dependency retrieval was network-blocked in prior P7 verification; gitleaks/download fallback is unavailable. This is not recorded as PASS. |
| `test_vllm_version_is` | NOT RUN | Its expectation conflicts with the source-checkout `VLLM_VERSION=0.29.0` override required by this host environment. |

## 4. Acceptance interpretation

These results establish the local source/static/CPU contract for the exact P7 final
tree. They do **not** establish NPU physical reads, stream/event lifetime, live
async, cross-device-family behavior, performance, mixed serving safety, or Graph
support.

```text
EAGER STATIC/CPU CONTRACT: PASS
EAGER NPU VERIFIED: NO
EAGER PERFORMANCE VERIFIED: NO
```
