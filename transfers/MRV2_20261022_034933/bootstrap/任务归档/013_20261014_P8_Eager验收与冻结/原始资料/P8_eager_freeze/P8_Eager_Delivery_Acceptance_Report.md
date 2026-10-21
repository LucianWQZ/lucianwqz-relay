# MRV2 Draft Sliding Window — P8-E Eager Delivery Acceptance Report

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

## 1. Decision summary

P8-E accepts the exact P7 final tree as a **local/static delivery candidate**. No
P8 production correction was required and no P8 production commit was created.
Independent delivery review and this fact adjudication are complete. The regenerated
package is ready for the comprehensive company-server Eager NPU campaign, subject to
the owner-supplied model/device inputs recorded in the mandatory matrix.

This is not a runtime-support or release declaration. The positive rows remain
`READY_FOR_NPU`; `G-MIXED` is owner-blocked and release-blocking; Graph remains
frozen; real async is absent.

## 2. Exact baseline and source boundary

| Repository | Required and observed HEAD | Required and observed tree | Status |
|---|---|---|---|
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | clean, zero diff |
| vLLM-Ascend | `4753742ab181920292c504a79eedecf9b428ae1b` | `b7e525c3c9d45617ad1023ad45c6948c466a3631` | clean, zero diff |

The final vLLM-Ascend branch is `feature/p7-eager-completion`; P7 original is
`7feb6def...` and P6 final parent is `7599497...`. Git history contains the 16
linear delivery commits from base `841dc6cc...`; it contains no server debug commit,
upstream-hook prototype, P6A source commit, or P8 source commit.

Boundary audit:

- vLLM has no private patch or prototype API dependency;
- production modifications exist only in vLLM-Ascend;
- no module-global/ContextVar Window transport exists;
- no temporary Target/full-owner swap or slot override exists;
- no production install call exists for the P5/P6 Graph provider;
- P7 touched no Graph capture source;
- FULL, FULL_DECODE_ONLY and PIECEWISE remain rejected;
- COMPATIBILITY/310P fails before FullSource and cannot leak through class
  inheritance;
- unsupported capability decisions fail before live FullSource/workspace creation.

## 3. Track separation

Graph host-static identity and replay/update carrier work remains preserved in P5/P6,
but P6A found no authorized existing pre-capture seam. The owner declined new
vendor-local capture assembly and vLLM modification. P8 neither revisits nor works
around that decision.

```text
Eager: candidate paths may proceed only with effective graph mode NONE.
Graph: frozen, user Gate closed, no runtime support claim.
```

## 4. Accepted positive Eager candidates

Exactly three method families can reach `READY_FOR_NPU`:

1. normalized Eagle3 with configured static K;
2. normalized DFlash;
3. eligible non-DeepSeek-V4 co-trained DSpark with actual query width.

Every positive decision additionally requires:

- `AttentionBackendFamily.STANDARD`;
- one executable dense GQA/FIA direct-prefix group;
- graph NONE/enforce eager;
- async false;
- TP=DP=PP=PCP=DCP=1;
- SP, DSA-CP and FlashComm false;
- prefix cache off;
- no mixed/chunked Window proposal;
- valid P1 policy/math, P2 canonical FullSource/descriptor, P3 identity/lease/store,
  and P4 method-specific read consumer;
- exact P7 topology fingerprint enforcement.

The Draft read table and lengths may differ. Canonical FullSource, Target metadata,
absolute positions/query layout, full slot mapping and physical KV write remain
unchanged.

## 5. OFF and forced-OFF acceptance

`CONFIG_OFF` remains the original factory/dispatch behavior and creates no Window
plan, FullSource, workspace, P7 extension state, async Window pool, or Graph provider.
Target/write and Graph descriptor behavior remain baseline.

MTP and DeepSeek-V4 co-trained DSpark remain `FORCED_OFF` before numeric validation,
inventory, FullSource, workspace or P7 topology state. Their warning/baseline
contracts remain covered by P1–P7 regression. They are not negative-error Window
routes and must not enter Window infrastructure.

## 6. Honest negative matrix

- Owner blocked: plain Eagle, Eagle3 dynamic K, heterogeneous multi-group, general
  mixed serving.
- Fail closed: DFlash2; DSA-v1/compressor/QLI; SFA main/indexer; MLA; V4/V4.1
  compositions; native SWA/circular/chunked and recycling/offload; homogeneous
  multi-group; TP/DP/PP/PCP/DCP >1; SP; DSA-CP; FlashComm; prefix cache; Graph modes;
  COMPATIBILITY/310P.
- Static only: async true host ownership/state machine.

For complex backends and parallel routes, rejection is capability-time and occurs
before live FullSource/workspace allocation. The DCP helper correctly defines
`local_V = local_prefix(E) - local_prefix(S)`, but **MATH_READY is not LIVE_SUPPORT**.

## 7. Async acceptance

The host/static bounded pool proves generation, mapping epoch, ordered request,
topology, lane/operation ownership, delayed and reverse completion, pressure,
abort-before-submit, fail-closed abort-after-submit, stale-handle rejection,
backend-derived-buffer non-alias and topology drift rejection.

It does not have a production speculator binding or real NPU completion event.
Therefore:

```text
HOST/STATIC OWNERSHIP MODEL: PASS
LIVE SPECULATOR BINDING: ABSENT
REAL NPU COMPLETION EVENT: ABSENT
ASYNC LIVE: FAIL-CLOSED
STATUS: STATIC_READY
```

## 8. Serving blocker

Mixed prefill/decode still raises `NotImplementedError` before epoch creation. Server
evidence shows this can abort EngineCore, and there is no safe admission restriction.
No owner decision selects general-serving implementation or a single-active-request
product scope.

```text
G-MIXED: OWNER_BLOCKED
RELEASE IMPACT: BLOCKER
```

Implementing mixed serving or admission is a return to P7/owner scope, not a hidden
P8 fix.

## 9. Runtime evidence ruling

The prior P4 server evidence is retained but not promoted:

- Node133 A2/910B2, P4 final `1011e2c2...`;
- Eagle3 static K=3, W=64, TP1 eager, single active request;
- L3/L4 FIA operand and isolation evidence for 284 proposals / 852 active rows and
  33/33 exact Draft FIA samples.

It does not transfer to P7 final, DFlash, DSpark, A3/A5, batch>1, true persistent
row reuse, kernel-level physical reads, real async, lifetime, performance or release.
Sequential A/B/A-style evidence does not prove row reuse. Node101/A3 evidence is
not available. See `P8_Eager_Runtime_Evidence_Ledger.md`.

## 10. Local verification

The detailed command/result ledger is `P8_Local_Test_Results.md`.

- exact nine-file targeted P1–P7 and graph-host command: `360 passed` (the complete
  command is recorded in `P8_Local_Test_Results.md`);
- full spec_decode: `588 passed, 13 skipped, 7 retained VWN host failures`;
- attention, distributed (outside socket-restricted sandbox), worker/v2,
  BlockTables, attn_utils/attention_v1, 310P and relevant config/patch suites pass;
- Ruff, format, targeted Mypy, compileall, diff-check and locally executable hooks
  pass;
- full Ascend config construction remains host/platform-environment blocked and is
  not reported as PASS.

## 11. Freeze reproducibility

The complete range is packaged as a binary-safe full diff, 16 ordered format
patches and an incremental Git bundle. Independent temporary-checkout tests proved:

- `git apply --check` and full-diff `git write-tree` equality;
- complete `git am` series tree equality;
- `git bundle verify`, fetch into a clean exact-base repository, exact final SHA and
  tree equality;
- clean restored trees.

Because the local source is shallow and network unshallow was unavailable, the
bundle explicitly requires base `841dc6cc...`; it is not a standalone-clone bundle.
See `P8_Freeze_Reproducibility_Report.md`.

## 12. Delivery artifacts

- final and owner-mandatory support matrices;
- runtime evidence and remaining Gate ledgers;
- executable comprehensive NPU campaign;
- performance methodology;
- online Eager debug playbook plus frozen-Graph appendix;
- release risk register;
- independent delivery review and this adjudication record;
- post-review clean-room restoration report;
- P0–P7 snapshot and commit manifest;
- canonical Notes, P4 validation evidence, server evidence and prior P4 freeze;
- full diff, format patches, incremental bundle and `SHA256SUMS`.

## 13. Items explicitly returned to P7 or owner

- mixed/general serving implementation or single-request admission policy;
- live async binding and real completion lifecycle;
- complex-backend read contracts;
- parallel data-plane projection/consumers;
- any Graph pre-capture implementation or repository-boundary change.

P8 made no attempt to hide those capabilities in packaging or tests.

## 14. Final local verdict

```text
P8-E LOCAL ACCEPTANCE: PASS
EAGER STATIC/CPU CONTRACT: PASS
EAGER CAPABILITY MATRIX: COMPLETE
READY FOR COMPREHENSIVE EAGER NPU: YES

EAGER NPU VERIFIED: NO
EAGER PERFORMANCE VERIFIED: NO

G-MIXED: OWNER_BLOCKED
OWNER MANDATORY MATRIX: PARTIAL

GRAPH TRACK: FROZEN
GRAPH USER GATE: STILL FAIL-CLOSED
GRAPH REQUIREMENT: PRESERVED

EAGER RELEASE: HOLD
FULL FEATURE RELEASE: HOLD
```

`PASS` here means the local delivery contract and reproducible package are sound.
It does not mean the Feature is supported or releasable.

# Independent Review Resolution

## Review metadata

- Review: `P8_Eager_DeepSeek_Independent_Delivery_Review.md`
- Review date: 2026-10-14
- Adjudicated source: vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c`;
  vLLM-Ascend `4753742ab181920292c504a79eedecf9b428ae1b`
- Production action: none. All accepted issues were delivery-document or evidence
  corrections; final SHA/tree are unchanged.

## Resolution table

| ID | Severity | Finding | Reproduction | Resolution | Evidence | Action |
|---|---|---|---|---|---|---|
| m-01 | Minor | Four artifacts stated that 310P startup admits only MTP. | `patch_spec_decode_310.py::_init_speculator_310p` returns `_orig_init_speculator(...)` for every non-MTP route; `_init_speculator_baseline` has no 310P-only method gate. | `ACCEPTED` | The Window-specific COMPATIBILITY Gate still rejects before FullSource, so status remains `FAIL_CLOSED`; only the explanatory startup claim was false. | Corrected Support/Owner/Risk/NPU artifacts and the Plan. |
| m-02 | Minor | The `360 passed` targeted count lacked an exact file list. | The exact nine-file command now recorded in `P8_Local_Test_Results.md` was rerun and produced `360 passed, 1 warning`. | `ACCEPTED` | The review's alternative 9/13-file selections were different scopes; the original count is valid but was not reproducible from the old prose. | Added complete command and tied every summary to it. |
| m-03 | Minor | DSP-02 did not explain how `sample_from_anchor=false` is supplied. | Upstream DSpark and Ascend proposer both read `draft_model_config.hf_config.sample_from_anchor`, defaulting true; no dedicated CLI switch exists. | `ACCEPTED` | Exact constructors: upstream `DSparkSpeculator.__init__` and Ascend `DSparkProposer.__init__`. | NPU plan now requires an immutable owner-approved draft checkpoint/revision with resolved HF config false and archived hash; missing input is not a test PASS/FAIL. |
| m-04 | Minor | Debug playbook lacked a standalone slot-pollution/write-side path. | Read-carrier `_get_fia_params` is not the KV writer. Actual writers consume `attn_metadata.slot_mapping` in `AscendAttentionBackendImpl.reshape_and_cache` and the NZ `_reshape_and_cache`; slots originate in `BlockTables.compute_slot_mappings`. | `ACCEPTED` | Independent full-table + absolute-position slot recomputation must be compared with metadata and actual write operand. | Added a dedicated full-slot/physical-write diagnostic layer with first-divergence and forbidden-workaround rules. |
| m-05 | Minor | Parallel/flag negative cases lacked copyable arguments. | Pinned CLI exposes TP/DP/PP/PCP/DCP, async and prefix flags; SP is derived from EP + all2all + TP/DP; DSA-CP/FlashComm are Ascend additional-config/environment modes. | `ACCEPTED` | `arg_utils.py`, `ParallelConfig.use_sequence_parallel_moe`, `ascend_config.py`, and runtime-context extraction. | Added §2.1 argument map, prerequisites, expected diagnostics, and JSON-merge rules. |
| m-06 | Minor | DFlash/DSpark positive cases have no concrete model identities. | No owner-approved immutable pair is present in the package or source; inventing one would make the campaign less auditable. | `OWNER_BLOCKED` | OM-02/OM-03 already require product selection; static route readiness does not select a checkpoint. | Added explicit owner-input precondition, realpath/revision/hash requirements, and `OWNER_INPUT_MISSING` classification. |
| Q-01 | Question | Server debug SHA `2a485613...` cannot be inspected locally. | `git cat-file -t 2a485613` fails; it is neither a production ancestor nor an object in the bundle. | `INSUFFICIENT_EVIDENCE` | Production non-contamination is proven, but the server-only instrumentation diff cannot be code-audited from this delivery. | Evidence ledger and manifest now state the limitation; no debug artifact was fabricated. |
| Q-02 | Question | `test_ascend_config.py` pass count was inconsistent. | Exact rerun: `51 passed, 71 failed, 13 subtests passed`; 70 failures are device inference and one is missing `_build_info`. | `ACCEPTED` | The former `83 passed` figure conflated the file with a separate 32-test group. The suite remains environment-blocked, not PASS. | Corrected all P8/Plan result ledgers; retained the failures as limitations. |
| Q-03 | Question | Mandatory product choices remain open. | No signed decision selects model pairs/devices/W/K, general serving versus early admission, or release evidence thresholds. | `OWNER_BLOCKED` | Owner Matrix remains `PARTIAL`; G-MIXED remains a release blocker. | No implementation or guessed decision; handoff lists exact owner inputs. |

Statistics: `ACCEPTED=6`, `PARTIALLY_ACCEPTED=0`, `REJECTED=0`,
`INSUFFICIENT_EVIDENCE=1`, `DEFERRED_TO_NPU=0`, `OWNER_BLOCKED=2`,
`RETURN_TO_P7=0`.

## Final adjudication test evidence

| Scope | Final result | Classification |
|---|---:|---|
| Exact nine-file P1–P7 targeted | `360 passed, 1 warning` | PASS |
| Full `tests/ut/spec_decode` | `588 passed, 13 skipped, 7 failed, 2 subtests passed` | NOT full PASS; the seven retained VWN failures stop at upstream `selector.py:208` with no Window frame |
| Full attention | `472 passed, 3 skipped, 24 subtests passed` | PASS |
| Full distributed | sandbox: `571 passed, 1 error`; approved localhost rerun: `572 passed, 284 subtests passed` | PASS outside socket-restricted sandbox |
| worker/v2 + block table | `37 passed, 39 subtests passed` | PASS |
| attn_utils + attention_v1 | `86 passed, 2 subtests passed` | PASS |
| Full 310P | `155 passed, 2 skipped, 5 subtests passed` | PASS |
| `test_ascend_config.py` | `51 passed, 71 failed, 13 subtests passed` | Environment-blocked; not PASS |
| Ruff / format / targeted Mypy / compileall / diff-check | PASS | Exact base-to-final production range |

## Final review verdict

```text
P8-E LOCAL ACCEPTANCE: PASS
EAGER STATIC/CPU CONTRACT: PASS
EAGER CAPABILITY MATRIX: COMPLETE
READY FOR COMPREHENSIVE EAGER NPU: YES

EAGER NPU VERIFIED: NO
EAGER PERFORMANCE VERIFIED: NO

G-MIXED: OWNER_BLOCKED / RELEASE_BLOCKER
OWNER MANDATORY MATRIX: PARTIAL

GRAPH TRACK: FROZEN
GRAPH USER GATE: STILL FAIL-CLOSED
GRAPH REQUIREMENT: PRESERVED

EAGER RELEASE: HOLD
FULL FEATURE RELEASE: HOLD
```
