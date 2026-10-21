# P7-X MRV2 Draft Sliding Window — Performance Optimization Report

## A. Verdict

```text
OPTIMIZATION_IMPLEMENTED
SERVER REVALIDATION REQUIRED
NPU PERFORMANCE VERIFIED: NO
GRAPH TRACK: FROZEN
PUSH STATUS: NOT PUSHED
```

The source audit found three objectively avoidable Window-only operations. The
delivered patch removes only those operations; it does not change policy,
Window math, visible KV, method coverage, topology coverage, or completion
correctness.

## 1. Exact source identity

| Item | Value |
|---|---|
| vLLM-Ascend parent | `c1c2129aa49ee1de381130729de73124a6ec893a` |
| Parent tree | `384af8a0466f6aea2e73d6217f9802415b5ccd40` |
| Branch | `perf/p7x-draft-window-hotpath` |
| Performance commit | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |
| Final tree | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` |
| Commit subject | `perf(spec-decode): reduce MRV2 draft window hot-path overhead` |
| Signed-off-by | `Lucian <2207456347@qq.com>` |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |

The pinned vLLM checkout remained clean and was not modified. No Graph source,
MRV1 source, scheduler source, or public capability matrix was changed.

## B. Root-cause assessment

### PROVEN

- Eligible DSpark materializes one Window per outer proposal, not K times.
- Window ON performs a correctness-required exact-length D2H snapshot once per
  proposal. This patch does not remove or weaken it.
- The parent implementation cleared every workspace backing both immediately
  before successful materialization and again at retirement. Construction,
  normal retirement, and exception cleanup already establish a zeroed lane, so
  the pre-clear was duplicate work.
- `acquire_with_backpressure()` queried submitted completion events before
  attempting to use an already-free lane.
- `build_prefix_resident_snapshot()` cloned the result of
  `gather_valid_num_blocks_cpu()`, although that gather already allocates and
  returns a new caller-owned tensor.
- No hot-loop logger and no repeated capability/provider inventory were found.
  Capability dispatch is initialization-time state.

### LIKELY

Constant Window control-plane work is easier to observe at 16K, while the
attention-read saving dominates it at 128K. This is consistent with Node101,
but the existing four-request sample cannot quantify each component.

### POSSIBLE

The exact-length D2H may remain the largest constant Window-only cost. Reusing
the model runner's separate host snapshot would require a typed,
generation-bound ownership/timing seam and NPU ordering evidence. It was not
changed in this round.

### NOT SUPPORTED

- The evidence does not support calling the 16K result a deterministic 10%
  MRV2 regression.
- No source path was found where Window ON disables DSpark's MRV2 parallel
  forward, Markov sampler, EP path, or another identified OFF optimization.
- The four-request `-0.83%` result is not enough to distinguish overhead from
  noise.

## C. Exact changed files and functions

| File | Function/test | Change | Why safe |
|---|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window.py` | `DraftWindowWorkspace.materialize` | Removed the unconditional `_zero_all()` immediately before the write transaction. Retirement still performs the original full clear; exception recovery still performs a full clear. | A lane cannot materialize while bound. New lanes are zero-initialized; every normal release and every partial-write exception zeroes the lane. |
| `vllm_ascend/worker/v2/spec_decode/draft_window_async.py` | `DraftWindowEagerAsyncPool.acquire_with_backpressure` | Attempts normal acquire first. It polls/reclaims only after real pool pressure, retries, then preserves the existing oldest-event wait path. | Free backing is never overwritten. Pressure, reverse completion, wait failure, abort, and stale-handle rules are unchanged. |
| `vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py` | `build_prefix_resident_snapshot` | Removed `.clone()` from the fresh CPU gather result. | `gather_valid_num_blocks_cpu()` creates a new zero tensor and fills it; it does not return borrowed FullSource storage. |
| `tests/ut/spec_decode/test_draft_window_runtime.py` | `test_workspace_success_path_avoids_redundant_preclear` | Locks one full cleanup per successful generation and verifies all backing is zero after retirement. | Protects zero-tail and reuse semantics while detecting reintroduced duplicate clearing. |
| `tests/ut/spec_decode/test_draft_window_async.py` | fake token instrumentation and `test_backpressure_acquire_does_not_poll_when_a_lane_is_free` | Locks zero additional query/wait when another lane is free. | Existing pressure and reverse-completion tests continue to protect the slow path. |
| `tests/ut/spec_decode/test_draft_window_nongraph.py` | `test_prefix_resident_snapshot_takes_ownership_of_fresh_gather` | Locks direct ownership transfer of the fresh gather tensor. | Detects an accidental clone without weakening resident-set freshness tests. |

Final source anchors are approximately:

- workspace transaction: `draft_window.py:1737-1804`;
- retirement cleanup: `draft_window.py:1828-1844`;
- async acquisition: `draft_window_async.py:203-269`;
- resident snapshot: `draft_window_nongraph.py:200-228`.

## D. Hot-path before/after

| Operation | Parent frequency | Final frequency | Saving / status |
|---|---:|---:|---|
| Window scalar/row plan | 1 per proposal | 1 per proposal | unchanged; correctness-required |
| exact Draft seq-length D2H | 1 per proposal | 1 per proposal | unchanged; correctness-required |
| full workspace cleanup on successful generation | 2 | 1 | one full table/count/length clear sequence removed |
| canonical row-slice table copy | 1 per active row/proposal | same | unchanged; source can change without S changing |
| CPU valid-count gather allocation | 1 | 1 | unchanged |
| CPU valid-count clone after gather | 1 | 0 | one tensor allocation/copy removed |
| event query before a free-lane acquire | one per submitted lane | 0 | deferred until actual bounded-pool pressure |
| pressure reclaim/retry | on pressure | on pressure | unchanged |
| oldest completion wait | on unresolved pressure | same | unchanged |
| provider/capability dispatch | init only | init only | no hot-path change needed |
| metadata build/isolation | 1 per proposal | same | unchanged |

### Rejected optimization experiment

An intermediate prototype narrowed retirement cleanup to the prior active table
prefix. Although correctness tests passed, its non-contiguous prefix zero was
about 4% slower in the initial CPU proxy run. It was removed before commit.
The committed workspace change is deliberately narrower: eliminate only the
duplicate pre-clear and retain the original contiguous full reset.

## E. Test evidence

### Red-to-green

The final three new tests were applied to the exact parent worktree before the
production patch:

```text
3 failed

workspace: full_clear_calls was 2, expected 1
async: query_calls advanced from 1 to 2 despite a free lane
resident snapshot: returned tensor was a clone, not the fresh gather owner
```

At the final commit:

```text
3 passed
```

### Functional and regression tests

| Scope | Result | Limitation |
|---|---|---|
| Required P7-X targeted files plus `attn_utils_v2` | `364 passed` | CPU/host contract only |
| Directly affected runtime/async/non-Graph files | `73 passed` | CPU/host contract only |
| BlockTables + attention_v1 | `55 passed`, `23 subtests passed` | no NPU kernels |
| Full `tests/ut/spec_decode` | `621 passed, 13 skipped, 7 failed`, `2 subtests passed` | Seven VWN failures stop in pinned upstream `selector.py` with `Invalid attention backend for None` |
| Parent comparison for VWN file | same `7 failed, 2 passed` | proves the seven host failures pre-exist this patch |

The seven full-suite failures are not reported as PASS. Their stacks do not
cross any file changed by this commit and reproduce at the exact parent.

### Static checks

| Check | Result |
|---|---|
| Ruff on six changed files | PASS |
| Ruff format check | PASS |
| Targeted Mypy (`--follow-imports=skip`) | PASS: 3 source files |
| `compileall` for spec_decode source/tests | PASS |
| `git diff --check` | PASS |
| Relevant pre-commit hooks | Ruff, format, codespell, typos, filename, init, logger, forbidden-import, boolean-context, long-function, symbolic-meta all PASS |
| actionlint hook environment | NOT RUN: Go dependency download timed out at `proxy.golang.org`; no workflow file changed |
| gitleaks hook | NOT RUN: host has neither `gitleaks` nor `wget`; diff contains only the six audited Python files |

## F. Local microbenchmark

### Method

- exact parent and final code were run from separate worktrees;
- same Mac host, Python environment, input objects, warmup, and iteration count;
- seven measured rounds; table reports median nanoseconds per operation;
- workspace cases: 30 warmup + 7 × 300 measured iterations;
- async and resident cases: 100 warmup + 7 × 3000 measured iterations;
- W=1024, K=8, batch=1 cases use the existing test-fixture B=64
  direct-prefix geometry at exact lengths 16,000 and 128,000;
- B=64 is a test-fixture geometry, not a claim about an unobserved GLM runtime
  block geometry;
- an additional 16-row, 1024-column capacity case stresses workspace
  bookkeeping.

| Case | Parent median | Final median | Delta |
|---|---:|---:|---:|
| workspace materialize+retire, batch=1, E=16K | 40,258.61 ns | 39,489.31 ns | -1.91% |
| workspace materialize+retire, batch=1, E=128K | 40,103.89 ns | 39,621.39 ns | -1.20% |
| workspace materialize+retire, 16×1024 capacity | 79,160.28 ns | 79,612.92 ns | +0.57% (noise / no gain claimed) |
| async acquire while another lane is free | 4,809.08 ns | 4,054.13 ns | -15.70% |
| prefix resident snapshot, 8 rows | 5,046.31 ns | 4,721.26 ns | -6.44% |

The async benchmark also counted completion queries over warmup plus measured
iterations:

```text
parent: 21,101
final:       1  (the initial submit-time correctness query)
```

These are host bookkeeping measurements, not NPU latency or throughput proof.
They show that the intended operations disappeared and that no broad local
regression was exposed. Only Node101 can determine end-to-end value.

## G. Frozen invariant audit

| Invariant | Result |
|---|---|
| Window changes Draft READ only | preserved |
| canonical FullSource/full table | unchanged and read-only |
| slot mapping | unchanged, full, absolute |
| positions/query layout | unchanged |
| physical KV write | unchanged, full/absolute |
| Target metadata/history | unchanged |
| S/E/V math and descriptor source | unchanged |
| mapping epoch/request fingerprint | unchanged |
| stale generation rejection | unchanged |
| async lane ownership | unchanged and bounded |
| pressure/reverse completion/abort behavior | existing tests pass |
| CONFIG_OFF/FORCED_OFF state allocation | unchanged: zero Window runtime state |
| MTP forced OFF | unchanged |
| DeepSeek-V4 co-trained DSpark forced OFF | unchanged |
| eligible DSpark/DFlash/Eagle3 method contract | unchanged |
| Graph | frozen; no Graph file or gate changed |
| vLLM | exact pinned checkout, no modification |
| MRV1 | untouched |

## H. Risks and limits

1. A completed async lane can remain owned while another lane is free; it is
   reclaimed on the first real pressure event. Ownership and memory remain
   bounded, but retention may last one additional operation.
2. Removing the pre-clear relies on the existing lifecycle invariant that
   construction, retirement, and exception cleanup leave an unbound workspace
   zeroed. The new test locks this invariant; bypassing the runtime owner would
   still be invalid usage.
3. Removing the clone relies on `gather_valid_num_blocks_cpu()` continuing to
   return fresh storage. The ownership regression test locks that contract.
4. The exact-length D2H, required table copy, metadata build, and isolation walk
   remain. This is intentionally not a claim that Window overhead is eliminated.
5. No A3/NPU run was performed. NPU event-query cost, stream interaction, D2D
   clear cost, end-to-end throughput, and the 128K success guard remain open.

## I. New SHA and tree

```text
branch:
perf/p7x-draft-window-hotpath

commit:
1b7215c37d1e3c9d1edac1fc20bcad26917ca251

tree:
9a6c38c0e92853b462cd1f05aa5f70244f82a72f

push:
NOT PUSHED
```

## J. Node101 handoff

```text
SERVER REVALIDATION REQUIRED
```

Use the exact performance commit above and the same GLM-5.2-W4A8 / DSpark K8 /
TP16 / DP1 / EP-on / async-on / Draft-eager configuration.

### 16K primary campaign

Run either:

```text
OFF -> W1024 -> OFF -> W1024
```

or equivalent randomized A/B/A ordering. Each cell should repeat at least
three times; use `data_num > 4` if cost permits. Preserve raw latency,
acceptance, throughput, event/profile, and expanded argv artifacts. The goal is
to decide whether `-0.83%` was noise and whether the removed control-plane work
is visible—not to force a historical +10% target.

### 128K regression guard

Repeat OFF and W1024. The current success reference is:

```text
W1024 acceptance ~= 6.05
throughput       ~= 26.87 tok/s
TPOT             ~= 12.2 ms
```

Any statistically meaningful regression in correctness, physical read-set,
slot/Target invariants, lifetime, or 128K throughput blocks adoption of this
performance commit.
