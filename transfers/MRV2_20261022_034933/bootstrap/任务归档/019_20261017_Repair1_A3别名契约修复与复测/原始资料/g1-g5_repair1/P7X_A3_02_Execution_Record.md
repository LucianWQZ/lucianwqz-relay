**# P7X_A3_02_Execution_Record**


RUN_ID: `20261019_055109_13373fff`

RUN_ROOT: `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff`

Timezone: Asia/Shanghai (UTC+08:00)


This record is generated from `commands/ledger.jsonl`. Every important command has a

`CMD-xxxx` entry with cwd, argv, selected env, pid/pgid, device, exit code,

stdout/stderr source and notes. Expected nonzero exits are marked explicitly.


**## Command ledger**


| CMD | case | attempt | start | end | cwd | device | rc | result | stdout | notes |

|---|---|---|---|---|---|---|---|---|---|---|

| CMD-0001 | PREFLIGHT | 1 | 2026-10-19T05:52:41.523123+08:00 | 2026-10-19T05:52:41.523123+08:00 | `/home` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/preflight_before.txt` | Bootstrap preflight snapshot |

| CMD-0002 | PREFLIGHT | 1 | 2026-10-19T05:52:41.523123+08:00 | 2026-10-19T05:52:41.523123+08:00 | `/` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0002.stdout.log` | Old input availability; result printed to console |

| CMD-0003 | PREFLIGHT | 1 | 2026-10-19T05:52:41.523123+08:00 | 2026-10-19T05:52:41.523123+08:00 | `/` | none | 0 | OK | `console` | Remote tip = 13373fff637e819f3db125e05064f94cba3475a3 |

| CMD-0004 | RECOVERY | 1 | 2026-10-19T05:53:23.162579+08:00 | 2026-10-19T05:53:58.362112+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0004.stdout.log` | Copy old campaign recoverable inputs into reference/ (read-only source). |

| CMD-0005 | RECOVERY | 1 | 2026-10-19T05:54:35.590789+08:00 | 2026-10-19T05:55:57.211750+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0005.stdout.log` | Recompute fixture key hashes and all target shards; compare with provided manifest. |

| CMD-0006 | SOURCE | 1 | 2026-10-19T05:57:20.145043+08:00 | 2026-10-19T05:58:17.581602+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0006.stdout.log` | Clone exact vllm-ascend branch and detach at 13373fff; verify SHA/tree/parent/clean. |

| CMD-0007 | SOURCE | 1 | 2026-10-19T05:58:54.481709+08:00 | 2026-10-19T05:59:28.436505+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0007.stdout.log` | Independent vLLM checkout from trusted local complete object store; verify pinned SHA/tree/clean. |

| CMD-0008 | RUNTIME | 1 | 2026-10-19T06:05:31.050427+08:00 | 2026-10-19T06:06:05.361264+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0008.stdout.log` | Build run-local overlay: exact 13373fff Python + A3 donor non-Python. |

| CMD-0009 | RUNTIME | 1 | 2026-10-19T06:06:50.162199+08:00 | 2026-10-19T06:07:42.207636+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0009.stdout.log` | Import provenance: all 12 required modules must resolve under run-local overlay. |

| CMD-0010 | RUNTIME | 2 | 2026-10-19T06:09:10.500583+08:00 | 2026-10-19T06:09:58.206463+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0010.stdout.log` | Re-run provenance with symlink-aware pinned-source check; JSON written to manifests. |

| CMD-0011 | HOST_UT | 1 | 2026-10-19T06:10:34.838677+08:00 | 2026-10-19T06:11:28.714054+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_characterization.log` | Host UT test_draft_window_graph_characterization |

| CMD-0012 | HOST_UT | 1 | 2026-10-19T06:11:28.763031+08:00 | 2026-10-19T06:12:21.919523+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_carrier.log` | Host UT test_draft_window_graph_carrier |

| CMD-0013 | HOST_UT | 1 | 2026-10-19T06:12:21.969374+08:00 | 2026-10-19T06:13:14.727324+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_binding.log` | Host UT test_draft_window_graph_binding |

| CMD-0014 | HOST_UT | 1 | 2026-10-19T06:13:14.775323+08:00 | 2026-10-19T06:14:07.611561+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_oracle.log` | Host UT test_draft_window_graph_oracle |

| CMD-0015 | HOST_UT | 1 | 2026-10-19T06:14:43.912753+08:00 | 2026-10-19T06:15:37.460067+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/real_owner_regression.log` | Explicit real-owner regression tests |

| CMD-0016 | OBS_READINESS | 1 | 2026-10-19T06:16:19.425044+08:00 | 2026-10-19T06:16:52.992108+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0016.stdout.log` | Read real helper/profiler capability; no command invention. |

| CMD-0017 | A0 | 1 | 2026-10-19T06:20:49.442173+08:00 | 2026-10-19T06:23:37.875629+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A0/driver.log` | A0: window OFF, experimental flag 0, exact old prompt/seed/sampling. Expect OK and zero characterization state. |

| CMD-0018 | A1 | 1 | 2026-10-19T06:24:26.950095+08:00 | 2026-10-19T06:26:04.763443+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 2 | NONZERO_EXIT | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A1/driver.log` | A1: W=1024, experimental flag 0. Expected GRAPH_FROZEN before FullSource/workspace/provider/capture carrier. |

| CMD-0019 | B | 1 | 2026-10-19T06:26:53.179697+08:00 | 2026-10-19T06:28:09.887966+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 2 | NONZERO_EXIT | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/driver.log` | B: W=1024, experimental flag 1, v2 artifact. Expect old alias failure fixed and real replay. |

| CMD-0020 | B_DIAG_CAP7 | 1 | 2026-10-19T06:30:45.441007+08:00 | 2026-10-19T06:32:31.778190+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap7/driver.log` | DIAGNOSTIC_NOT_FIXTURE_CONTRACT: single capture size [7] to isolate observer reuse across descriptors. |

| CMD-0021 | B_DIAG_CAP14 | 1 | 2026-10-19T06:34:12.345477+08:00 | 2026-10-19T06:35:58.558890+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap14/driver.log` | DIAGNOSTIC_PARTIAL_INVENTORY: capture size [14], 2 requests, targets real (2,14) Graph bucket. |

| CMD-0022 | B_DIAG_CAP28 | 1 | 2026-10-19T06:36:55.128705+08:00 | 2026-10-19T06:38:36.812413+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28/driver.log` | DIAGNOSTIC_PARTIAL_INVENTORY: capture size [28], 4 requests, real (4,28) Graph bucket. |

| CMD-0023 | B_DIAG_CAP28_INTROSPECT | 1 | 2026-10-19T06:39:41.303831+08:00 | 2026-10-19T06:41:02.757826+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28_introspect/driver.log` | Read-only capture inventory introspection for capture size [28]; max_tokens=1. |

| CMD-0024 | B_DIAG_CAP24_INTROSPECT | 1 | 2026-10-19T06:42:03.516984+08:00 | 2026-10-19T06:43:35.728065+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | 5 | 2 | NONZERO_EXIT | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap24_introspect/driver.log` | Single size 24: target 24 (multiple of 8), draft round-up 28=(4,28). Read capture inventory. |

| CMD-0025 | HOST_LIFECYCLE | 1 | 2026-10-19T06:44:24.415030+08:00 | 2026-10-19T06:45:17.074232+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/host_lifecycle.log` | Host bind/publish/A-B-A'/operator-boundary/G4/G5/auditor tests on exact 13373fff source. |

| CMD-0026 | NEGATIVE | 1 | 2026-10-19T06:45:57.785126+08:00 | 2026-10-19T06:46:46.091032+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/negative/negative_matrix_cpu.log` | CPU negative/eligibility matrix on exact 13373fff source. |

| CMD-0027 | G3_ORACLE_HOST | 1 | 2026-10-19T06:47:25.136479+08:00 | 2026-10-19T06:48:00.096632+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/G3/oracle_cases.log` | Independent host oracle cases: short/boundary/non-boundary/long/source-shortage/nonzero-offset. |

| CMD-0028 | MANIFEST | 1 | 2026-10-19T06:52:30.944667+08:00 | 2026-10-19T06:53:04.425113+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0028.stdout.log` | Assemble source/runtime/fixture manifests. |

| CMD-0029 | CROSS_AUDIT | 1 | 2026-10-19T06:54:20.030607+08:00 | 2026-10-19T06:54:54.161637+08:00 | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff` | none | 0 | OK | `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/reports/independent_checker.log` | Independent cross-artifact checker (read-only). |


**## Expanded argv for key commands**


**### CMD-0004 — RECOVERY attempt 1**


```text

argv:

  bash

  -lc


set -euo pipefail

R=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

O=/mnt/wenqing/mrv2_graph_g1g5_campaign

P=/home/wenqing/mrv2_graph_g1g5

mkdir -p "$R/reference/old_campaign" "$R/reference/old_workroot"

cp -a "$O/manifests" "$R/reference/old_campaign/"

cp -a "$O/commands" "$R/reference/old_campaign/"

cp -a "$O/requests" "$R/reference/old_campaign/"

cp -a "$O/negative" "$R/reference/old_campaign/"

cp -a "$O/G0_fixture" "$R/reference/old_campaign/"

cp -a "$O/G0_mrv2_identity" "$R/reference/old_campaign/"

cp -a "$O/G1_capture" "$R/reference/old_campaign/"

cp -a "$O/00_preflight" "$R/reference/old_campaign/"

cp -a "$O/00_tools" "$R/reference/old_campaign/"

cp -a "$P/runtime" "$R/reference/old_workroot/"

cp -a "$P/scripts" "$R/reference/old_workroot/"

echo "copied old inputs"

find "$R/reference/old_campaign" -type f | wc -l


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4117384 pgid=4117384

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0004.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0004.stderr.log

```


**### CMD-0005 — RECOVERY attempt 1**


```text

argv:

  bash

  -lc


set -euo pipefail

R=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

OUT="$R/manifests/model_hash_reverify.txt"

{

echo "# model hash reverify $(date -Is)"

for f in \\

 /mnt/share/wql/Qwen3-8B/config.json \\

 /mnt/share/wql/Qwen3-8B/model.safetensors.index.json \\

 /mnt/share/wql/Qwen3-8B/tokenizer.json \\

 /mnt/share/dspark_qwen3_8b_block7/config.json \\

 /mnt/share/dspark_qwen3_8b_block7/model.safetensors \\

 /mnt/share/wql/Qwen3-8B/model-0000*-of-00005.safetensors ; do

  [ -e "$f" ] && sha256sum "$f"

done

} > "$OUT"

cat "$OUT"


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4118559 pgid=4118559

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0005.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0005.stderr.log

```


**### CMD-0006 — SOURCE attempt 1**


```text

argv:

  bash

  -lc


set -euo pipefail

R=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

git clone --single-branch --branch fix/p7x-graph-base-a3-g1g5 \\

  https\://github.com/LucianWQZ/vllm-ascend.git "$R/src/vllm-ascend"

git -C "$R/src/vllm-ascend" checkout --detach 13373fff637e819f3db125e05064f94cba3475a3

echo "=== identity ==="

git -C "$R/src/vllm-ascend" show -s --format="%H%n%T%n%P%n%s" HEAD

echo "=== rev-parse ==="

git -C "$R/src/vllm-ascend" rev-parse HEAD

git -C "$R/src/vllm-ascend" rev-parse HEAD^{tree}

echo "=== status ==="

git -C "$R/src/vllm-ascend" status --porcelain --untracked-files=all | head -20

echo "status_count=$(git -C "$R/src/vllm-ascend" status --porcelain --untracked-files=all | wc -l)"


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4120333 pgid=4120333

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0006.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0006.stderr.log

```


**### CMD-0007 — SOURCE attempt 1**


```text

argv:

  bash

  -lc


set -euo pipefail

R=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

git clone --no-hardlinks --single-branch \\

  /home/wenqing/mrv2_graph_g1g5/src/vllm "$R/src/vllm"

git -C "$R/src/vllm" remote set-url origin https\://github.com/LucianWQZ/vllm.git

git -C "$R/src/vllm" checkout --detach 84030bbe3d74d99bad477a3d2e37a973ccd8865c

echo "=== identity ==="

git -C "$R/src/vllm" show -s --format="%H%n%T%n%P%n%s" HEAD

echo "=== status ==="

git -C "$R/src/vllm" status --porcelain --untracked-files=all | head -20

echo "status_count=$(git -C "$R/src/vllm" status --porcelain --untracked-files=all | wc -l)"

echo "=== provenance ==="

echo "clone_source=/home/wenqing/mrv2_graph_g1g5/src/vllm (verified exact pinned SHA/tree)"

echo "origin=https\://github.com/LucianWQZ/vllm.git"


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4121539 pgid=4121539

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0007.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0007.stderr.log

```


**### CMD-0008 — RUNTIME attempt 1**


```text

argv:

  bash

  -lc

  bash /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/build_overlay.sh

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4128804 pgid=4128804

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0008.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0008.stderr.log

```


**### CMD-0009 — RUNTIME attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1; python /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/probe_import_provenance.py > /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/manifests/import_provenance.json; tail -40 /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/manifests/import_provenance.json

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4129976 pgid=4129976

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0009.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0009.stderr.log

```


**### CMD-0010 — RUNTIME attempt 2**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1; python /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/probe_import_provenance.py

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4132039 pgid=4132039

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0010.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0010.stderr.log

```


**### CMD-0011 — HOST_UT attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1; python -m pytest -q tests/ut/spec_decode/test_draft_window_graph_characterization.py

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4133521 pgid=4133521

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_characterization.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_characterization.stderr.log

```


**### CMD-0012 — HOST_UT attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1; python -m pytest -q tests/ut/spec_decode/test_draft_window_graph_carrier.py

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4134483 pgid=4134483

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_carrier.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_carrier.stderr.log

```


**### CMD-0013 — HOST_UT attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1; python -m pytest -q tests/ut/spec_decode/test_draft_window_graph_binding.py

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4135408 pgid=4135408

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_binding.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_binding.stderr.log

```


**### CMD-0014 — HOST_UT attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1; python -m pytest -q tests/ut/spec_decode/test_draft_window_graph_oracle.py

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4136339 pgid=4136339

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_oracle.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/test_draft_window_graph_oracle.stderr.log

```


**### CMD-0015 — HOST_UT attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1; python -m pytest -vv tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_target_metadata_sharing_is_allowed_for_full_write_carriers tests/ut/spec_decode/test_draft_window_graph_carrier.py::test_draft_private_fields_still_reject_target_storage_alias

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4137884 pgid=4137884

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/real_owner_regression.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/real_owner_regression.stderr.log

```


**### CMD-0016 — OBS_READINESS attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

echo '=== helper help ==='; python tools/p7x_graph_g1_g5.py --help

echo '=== oracle help ==='; python tools/p7x_graph_g1_g5.py oracle --help

echo '=== audit help ==='; python tools/p7x_graph_g1_g5.py audit --help

echo '=== sample oracle ==='; python tools/p7x_graph_g1_g5.py oracle --full-table 1,2,3,4,5 --horizon 500 --exact 500 --upper 500 --window 1024 --legacy-block-size 128 --block-span 128 --query-width 7 --valid-block-count 5

echo '=== msprof ==='; command -v msprof || echo MSPROF_NOT_FOUND; msprof --help 2>&1 | head -40


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4139420 pgid=4139420

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0016.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0016.stderr.log

```


**### CMD-0017 — A0 attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=0

unset VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case A0 --window off --flag 0 --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A0/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4142265 pgid=4142265

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A0/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A0/driver.stderr.log

```


**### CMD-0018 — A1 attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=0

unset VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case A1 --window 1024 --flag 0 --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A1/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4145386 pgid=4145386

exit_code=2 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A1/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/A1/driver.stderr.log

```


**### CMD-0019 — B attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/artifact/B_artifact.json

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case B --window 1024 --flag 1 --artifact /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/artifact/B_artifact.json --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4147046 pgid=4147046

exit_code=2 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/driver.stderr.log

```


**### CMD-0020 — B_DIAG_CAP7 attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap7/artifact.json

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case B_DIAG_CAP7 --window 1024 --flag 1 --capture-sizes 7 --artifact /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap7/artifact.json --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap7/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4150501 pgid=4150501

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap7/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap7/driver.stderr.log

```


**### CMD-0021 — B_DIAG_CAP14 attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap14/artifact.json

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case B_DIAG_CAP14 --window 1024 --flag 1 --capture-sizes 14 --num-prompts 2 --artifact /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap14/artifact.json --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap14/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4153977 pgid=4153977

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap14/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap14/driver.stderr.log

```


**### CMD-0022 — B_DIAG_CAP28 attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28/artifact.json

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case B_DIAG_CAP28 --window 1024 --flag 1 --capture-sizes 28 --num-prompts 4 --artifact /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28/artifact.json --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4156365 pgid=4156365

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28/driver.stderr.log

```


**### CMD-0023 — B_DIAG_CAP28_INTROSPECT attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28_introspect/artifact.json

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case B_DIAG_CAP28_INTROSPECT --window 1024 --flag 1 --capture-sizes 28 --num-prompts 4 --max-tokens 1 --artifact /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28_introspect/artifact.json --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28_introspect/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4158792 pgid=4158792

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28_introspect/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap28_introspect/driver.stderr.log

```


**### CMD-0024 — B_DIAG_CAP24_INTROSPECT attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap24_introspect/artifact.json

export ASCEND_RT_VISIBLE_DEVICES=5

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/driver_case.py --case B_DIAG_CAP24_INTROSPECT --window 1024 --flag 1 --capture-sizes 24 --num-prompts 4 --max-tokens 1 --artifact /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap24_introspect/artifact.json --out /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap24_introspect/result.json


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=5

pid=4161154 pgid=4161154

exit_code=2 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap24_introspect/driver.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/B/diag_cap24_introspect/driver.stderr.log

```


**### CMD-0025 — HOST_LIFECYCLE attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

python -m pytest -vv   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_reuses_real_p3_generation_and_builds_private_metadata   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_update_operand_and_g4_records_are_machine_readable   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_fia_capture_call_records_actual_operator_operand   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_fia_update_call_records_rebound_operator_operand   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_replay_submission_records_real_event_without_synchronizing   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_campaign_auditor_requires_all_evidence_layers_and_detects_host_a_b_a   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_recorder_exception_releases_bound_carrier   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_runtime_candidate_host_a_b_a_refreshes_content_at_stable_address   tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_manager_prepares_candidate_before_consuming_graph_metadata   tests/ut/spec_decode/test_draft_window_graph_oracle.py


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4162845 pgid=4162845

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/host_lifecycle.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/host_tests/host_lifecycle.stderr.log

```


**### CMD-0026 — NEGATIVE attempt 1**


```text

argv:

  bash

  -lc


source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1

export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1

cd /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

python commands/negative_matrix_cpu.py


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4164379 pgid=4164379

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/negative/negative_matrix_cpu.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/negative/negative_matrix_cpu.stderr.log

```


**### CMD-0027 — G3_ORACLE_HOST attempt 1**


```text

argv:

  bash

  -lc


set -u

R=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

source $R/runtime/env_graph_char.sh >/dev/null 2>&1

cd $R/src/vllm-ascend

run() {

  name=$1; shift

  echo "=== CASE $name ==="

  python tools/p7x_graph_g1_g5.py oracle "$@" --output $R/G3/oracle_${name}.json

  echo "RC=$?"

}

run SHORT --full-table 1,2,3,4,5,6,7,8 --horizon 80 --exact 80 --upper 80 --window 1024 --legacy-block-size 128 --block-span 128 --query-width 7 --valid-block-count 8

run BOUNDARY --full-table 1,2,3,4,5,6,7,8 --horizon 1024 --exact 1024 --upper 1024 --window 1024 --legacy-block-size 128 --block-span 128 --query-width 7 --valid-block-count 8

run NONBOUNDARY --full-table 1,2,3,4,5,6,7,8 --horizon 1000 --exact 1000 --upper 1000 --window 1024 --legacy-block-size 128 --block-span 128 --query-width 7 --valid-block-count 8

run LONG --full-table 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 --horizon 2048 --exact 2048 --upper 2048 --window 1024 --legacy-block-size 128 --block-span 128 --query-width 7 --valid-block-count 16

echo "=== CASE SOURCE_SHORTAGE ==="

python tools/p7x_graph_g1_g5.py oracle --full-table 1,2,3,4,5,6,7,8 --horizon 2048 --exact 2048 --upper 2048 --window 1024 --legacy-block-size 128 --block-span 128 --query-width 7 --valid-block-count 8 --output $R/G3/oracle_SOURCE_SHORTAGE.json 2>&1 || echo "EXPECTED_REJECT_SOURCE_SHORTAGE rc=$?"

echo "=== CASE NONZERO_OFFSET ==="

python tools/p7x_graph_g1_g5.py oracle --full-table 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 --horizon 2048 --exact 2048 --upper 2048 --window 1024 --legacy-block-size 128 --block-span 96 --query-width 7 --valid-block-count 16 --output $R/G3/oracle_NONZERO_OFFSET.json 2>&1 || echo "EXPECTED_REJECT_NONZERO_OFFSET rc=$?"


env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/src/vllm-ascend

device_logical_id=none

pid=4165867 pgid=4165867

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/G3/oracle_cases.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/G3/oracle_cases.stderr.log

```


**### CMD-0028 — MANIFEST attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; python /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/assemble_manifests.py

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4170238 pgid=4170238

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0028.stdout.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/raw/CMD-0028.stderr.log

```


**### CMD-0029 — CROSS_AUDIT attempt 1**


```text

argv:

  bash

  -lc

  source /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/runtime/env_graph_char.sh >/dev/null 2>&1; python /mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/commands/independent_checker.py

env:

  PYTHONPATH=/usr/local/Ascend/cann-9.1.0/python/site-packages\:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages\:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:

  P7X_RUN_ROOT=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

cwd=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

device_logical_id=none

pid=4171572 pgid=4171572

exit_code=0 signal=None timeout=False

stdout=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/reports/independent_checker.log

stderr=/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff/reports/independent_checker.stderr.log

```


**## Phase notes**


- CMD-0001..0003: preflight, old-input availability, remote branch tip. Remote tip was exactly `13373fff`.

- CMD-0004: copied the recoverable previous-campaign inputs into `reference/` (read-only source).

- CMD-0005: re-hashed target config/index/tokenizer, all five target shards, draft config/weights; all matched the contract.

- CMD-0006: cloned `fix/p7x-graph-base-a3-g1g5` and detached at `13373fff`; SHA/tree/parent/clean verified.

- CMD-0007: independent pinned vLLM checkout from the verified local object store; SHA/tree/clean verified.

- CMD-0008: built run-local overlay from exact `13373fff` Python + A3 donor non-Python (618 py / 1269 non-py).

- CMD-0009/0010: import provenance; all required modules resolved to overlay or the pinned vLLM checkout (`provenance_ok=true`).

- CMD-0011..0015: four host UT files (116 tests) and the two real-owner regressions (2 tests) all PASS.

- CMD-0016: real helper/oracle/audit help and the independent oracle sample; no nonexistent subcommand invented.

- CMD-0017 (A0): window OFF, flag 0. OK; 16 tokens match the old contract; zero characterization/provider state.

- CMD-0018 (A1): W=1024, flag 0. Expected `GRAPH_FROZEN`; rc=2 is the expected early gate, not a harness failure.

- CMD-0019 (B fixed contract): W=1024, flag 1, `[7,14,28]`. New production defect at capture observer re-attach; rc=2; partial artifact 1 capture event.

- CMD-0020..0024 (diagnostics): `[7]`, `[14]`, `[28]` did not trigger Graph capture because the target manager had no capture descriptors; `[24]` failed characterization install because draft capture descriptors were empty. These are diagnostic attempts, not fixed-contract Base evidence.

- CMD-0025: 16 host lifecycle/A-B-A'/operator-boundary/G4/G5/auditor tests PASS.

- CMD-0026: CPU negative matrix 31/31 MATCH.

- CMD-0027: independent oracle SHORT/BOUNDARY/NONBOUNDARY/LONG PASS; SOURCE_SHORTAGE and NONZERO_OFFSET expected rejects.

- CMD-0028: assembled source/runtime/fixture manifests.

- CMD-0029: independent checker; first run 25 PASS / 1 OPEN (deliverables not yet written) / 0 FAIL.


**## Device / HBM notes**


- Preflight showed all 16 logical dies at \~3 GiB baseline; `mem_get_info` was used to select a free die rather than trusting `npu-smi` card labels.

- All device attempts used logical die 5; before each attempt the previous process had exited and HBM was allowed to release.

- One earlier rerun in the previous campaign raced HBM release; this run avoided that by waiting between attempts.


**## Final state**


- No campaign vLLM/driver/benchmark process remains (`pgrep` NONE).

- HBM released; `raw/npu_after.txt` saved.

- vllm-ascend `13373fff` / tree `739cde3d` clean; vLLM `84030bbe` / tree `f3e320f8` clean.

- Original team tools: 2296 files, path-keyed SHA256 comparison unchanged.

- No production source modification was made on the server.
