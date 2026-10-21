# P7-X Draft Window Graph Capture Patch — Local POC Report

## Outcome

```text
LOCAL_GRAPH_CAPTURE_SEAM_POC: PASS
GRAPH_SUPPORTED: NO
NPU: NOT RUN
PUBLIC GRAPH SUPPORT: STILL FROZEN
```

The local POC closes the Python/source-level startup metadata-carrier seam for
the single-group dense GQA/FIA DFlash and eligible DSpark capture path. It is a
local unpushed spike, not a production support commit.

## Exact identity

- Parent: `1b7215c37d1e3c9d1edac1fc20bcad26917ca251`
- Parent tree: `9a6c38c0e92853b462cd1f05aa5f70244f82a72f`
- Branch: `spike/p7x-draft-window-graph-patch`
- Local commit: `c43989aabd9b40a561987d39f4ba4516934f2f5b`
- Local tree: `5caecd1613206904a59960c23f22883115a9fd96`
- Pinned vLLM: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- Pinned vLLM tree: `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`
- vLLM changes: none
- Remote publication: none

## POC dataflow

```text
DFlashAclGraphManager.capture
  -> build typed context from exact manager capture descriptors
  -> attach context to speculator-owned Draft InputBuffers
  -> observe/validate explicit P6 capture provider
  -> upstream DFlashCudaGraphManager.capture
  -> patched _prepare_dflash_inputs_to_capture
  -> resolve exact P6 CaptureIdentity and persistent read carrier
  -> seed stable carrier backing for dummy capture geometry
  -> Ascend build_attn_metadata(
       block_tables = Window carrier for selected gid,
       seq_lens = Window device exact,
       seq_lens_cpu = Window CPU exact,
       seq_lens_cpu_upper_bound = Window upper,
       slot_mappings = canonical full dummy slots,
       query_start = baseline dummy query layout)
  -> AttentionState(Draft metadata, full layer slot mappings)
  -> finally remove context on success or exception
```

No context means an exact call to the saved upstream helper. The existing
Ascend `build_attn_metadata` worker patch remains the baseline behavior.

## Ownership and isolation

- The capture context belongs to one Draft `InputBuffers` instance.
- A foreign buffer or Target buffer is rejected.
- Two speculators cannot see each other's context or carrier address.
- The P6 provider owns persistent per-consumer backing.
- Startup capture uses `DraftWindowGraphCaptureIdentity`, never a fake runtime
  generation, request ID, or mapping epoch.
- A carrier already bound to a runtime generation is rejected at startup.
- Context use after cleanup is rejected.
- canonical FullSource content and storage do not alias Window backing.
- Target metadata is not transport for capture.

## Read/write invariant

Only Draft read carriers differ. Full slot mapping, absolute/write-side
ownership, query layout, and baseline positions owner stay unchanged. The
adapter never replaces `BlockTables`, `InputBuffers`, Target state, or any
module-global current owner.

## A–Q regression coverage

| ID | Contract | Result |
|---|---|---|
| A | patched helper symbol installed | pass |
| B | OFF delegates to exact saved original | pass |
| C | builder sees persistent Window table | pass |
| D | builder sees device/CPU exact and upper | pass |
| E | full slot-mapping identity preserved | pass |
| F | baseline query-start and positions owner preserved | pass |
| G | Window read storage does not alias canonical source; source content unchanged | pass |
| H | carrier address stable across repeated capture helper calls | pass |
| I | context owner is the Draft instance | pass |
| J | two fake speculators do not cross-talk | pass |
| K | stale descriptor rejected | pass |
| L | wrong capture bucket rejected | pass |
| M | runtime-bound generation rejected at startup capture | pass |
| N | context cleaned after successful capture | pass |
| O | context cleaned after capture exception | pass |
| P | PIECEWISE/skip-attention keeps full slots and does not build metadata | pass |
| Q | CONFIG_OFF creates no provider or context | pass |

DFlash and eligible DSpark are both parameterized through the shared route.

## Regression summary

```text
P5/P6 graph tests:
83 passed

full spec_decode spike:
635 passed, 13 skipped, 7 host-environment failures

full spec_decode unmodified parent:
621 passed, 13 skipped, same 7 host-environment failures

selected attn_utils/attention/DFlash/DSpark/DFlash2/Eagle graph tests:
174 passed, 2 subtests passed

ACL graph spike and parent:
24 passed, 3 identical host-platform failures, 2 subtests passed

Ruff / format / targeted Mypy / compileall / diff-check:
pass
```

The seven VWN failures are not reported as PASS. They fail before POC code at
the vLLM backend selector because this Mac host has no selected NPU attention
backend. The three ACL wrapper failures likewise reproduce on the parent and
arise because the host platform has no graph-pool handle.

## What this POC proves

- Existing vLLM-Ascend patch architecture can install the helper adapter once.
- The pinned caller needs no signature or source change.
- Draft-private `InputBuffers` is a viable instance-scoped context owner.
- Exact descriptor mapping can select a P6 persistent carrier.
- The Ascend builder can receive Window read inputs while full slots remain
  independent.
- OFF is exact delegation.
- replay/update source order is untouched.

## What this POC does not prove

- ACL Graph captured the persistent table/length addresses.
- An NPU operator physically read the intended Window token set.
- runtime content refresh is visible to the captured task.
- `UPDATE(N)` affects replay N or N+1.
- stream completion prevents early overwrite.
- TP16, async, prefix, parallel, complex backend, Eagle3, or performance.
- public Graph Window support.

## Product Gate audit

- `draft_window_eager_capability.py` still rejects every graph mode other than
  `NONE` before live Window materialization.
- `draft_window.py` retains the earlier Graph fail-closed boundary.
- P6 provider installation remains test-only; this spike adds no production
  auto-install point.
- public support matrices are unchanged.
- `run_fullgraph()` and `update_full_graph_params()` relative order is unchanged.

## Removal plan

Remove the private-helper patch when pinned/upstream vLLM exposes an explicit
vendor-neutral capture read-input provider. Until then, the patch must retain
source-drift tests around the exact helper signature and behavior.

## Recommendation

Keep the spike local and proceed only to the documented company-NPU evidence
campaign if the owner chooses to continue Graph characterization. Do not merge
or publish this branch as support evidence before G1–G7 close.

