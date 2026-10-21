# MRV2 Draft Sliding Window — P8-E Comprehensive Eager NPU Test Plan

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

This is an execution plan, not runtime evidence. It targets vLLM
`84030bbe3d74d99bad477a3d2e37a973ccd8865c` and vLLM-Ascend
`4753742ab181920292c504a79eedecf9b428ae1b`. No server experiment was run in P8-E.

## 1. Campaign prerequisites

For every machine, archive before launch:

```text
hostname, device model/family, firmware, driver, CANN, container image digest
vLLM path/SHA/tree/status
vLLM-Ascend path/SHA/tree/status
target and draft realpath + model revision/hash
fully expanded process argv and relevant environment
effective VllmConfig/AscendConfig/speculative/cache/parallel/compilation config
P7EagerTopologyFingerprint
request fixture token ids, seed and sampling config
```

The hardware profile must be `AttentionBackendFamily.STANDARD`. A2, A3 and A5
are independent campaigns. `COMPATIBILITY`/310P belongs to the negative campaign.

The package intentionally does not invent DFlash or DSpark checkpoint identities.
Before any `DFA-*` or `DSP-*` case is launched, the owner must sign an immutable
target/draft pair and provide, for both models, an absolute realpath, model revision,
`config.json` hash and architecture. Missing model identity is
`OWNER_INPUT_MISSING`, not a Window test failure and not permission to substitute an
unreviewed checkpoint.

## 2. Canonical launcher contract

The server owner must resolve actual model locations. A placeholder is not a run.

```bash
TARGET_MODEL=/absolute/server/path/to/target-model
DRAFT_MODEL=/absolute/server/path/to/draft-model
ARTIFACT_ROOT=/absolute/writable/path/P8_Eager_NPU/<case_id>

test -d "$TARGET_MODEL"
test -d "$DRAFT_MODEL"
realpath "$TARGET_MODEL"
realpath "$DRAFT_MODEL"

VLLM_USE_V1=1 \
vllm serve "$TARGET_MODEL" \
  --tensor-parallel-size 1 \
  --pipeline-parallel-size 1 \
  --enforce-eager \
  --seed 1024 \
  --speculative-config '{"method":"METHOD","model":"DRAFT_MODEL_REALPATH","num_speculative_tokens":K}' \
  --additional-config '{"draft_window_size":W}'
```

The campaign script must archive the fully expanded argv from `/proc/<pid>/cmdline`
or an equivalent source. It must also prove DP/PCP/DCP=1, SP/DSA-CP/FlashComm
off, async false, prefix cache off, and effective graph mode `NONE`.

For Window OFF/ON/A' comparisons, only `draft_window_size` may differ. Use
`temperature=0`, `n=1`, seed 1024 and fixed token-id fixtures. If the API rejects
an unrelated request form, classify `ENVIRONMENT_OR_FIXTURE_ERROR`, never PASS.

### 2.1 Negative-case argument map

Append exactly one dimension to an otherwise valid positive candidate unless a row
says the dimension is derived. Archive the expanded argv and effective config; a
launcher/resource failure is not a Gate pass.

| Dimension | Copyable argument fragment | Required interpretation |
|---|---|---|
| TP2 | `--tensor-parallel-size 2` | Diagnostic must include `TP=2`; requires two usable devices. |
| DP2 | `--data-parallel-size 2` | Diagnostic must include `DP=2`; archive the actual DP launch topology. |
| PP2 | `--pipeline-parallel-size 2` | Diagnostic must include `PP=2`; requires two usable stages/devices. |
| PCP2 | `--prefill-context-parallel-size 2` | Diagnostic must include `PCP=2`. |
| DCP2 | `--decode-context-parallel-size 2` | Diagnostic must include `DCP=2`; `MATH_READY` is not live support. |
| SP | `--tensor-parallel-size 2 --data-parallel-size 2 --enable-expert-parallel --all2all-backend allgather_reducescatter` | SP has no direct CLI flag. It is derived by `ParallelConfig.use_sequence_parallel_moe`; the reason may also include TP/DP. Use a compatible MoE fixture or classify setup failure honestly. |
| DSA-CP | merge `"enable_dsa_cp":true` into `--additional-config`, e.g. `'{"draft_window_size":W,"enable_dsa_cp":true}'` | Diagnostic must include DSA-CP; model/config prerequisites still apply. |
| FlashComm | merge `"enable_flashcomm1":true` into `--additional-config`, or set `VLLM_ASCEND_ENABLE_FLASHCOMM1=1` | Diagnostic must include FlashComm. This switch is deprecated; archive the warning and effective mode. Environment selects mode only and never transports generation state. |
| Async | `--async-scheduling` | Capability must be `STATIC_READY`, then live materialization must reject before FullSource. |
| Prefix | `--enable-prefix-caching` | Must fail closed before FullSource. |

For DSA-CP/FlashComm, replace rather than append a second
`--additional-config`: the final JSON must contain both `draft_window_size` and the
negative flag.

## 3. Required per-case artifact schema

Every case directory contains:

```text
manifest.json                 # machine, SHAs, trees, models, argv, env, topology
request.json                  # exact prompt token ids and sampling parameters
service.log
policy.jsonl                  # policy and capability decision
window_plan.jsonl             # L0/K/H/S and each E/V, or P4a equivalent
source_descriptor.jsonl       # gid, valid counts, source columns
window_table.jsonl            # full untruncated active rows + backing address
metadata.jsonl                # exact/upper/table identities and Draft store owner
operator.jsonl                # actual Draft and Target operator operands
slot_write.jsonl              # independent slot oracle and KV-write observation
target.jsonl                  # owner/content/length/logit oracle
lifecycle.jsonl               # generation, epoch, lane, event, retire/reuse timeline
profile/                      # raw profiler outputs when required
result.json                   # oracle-by-oracle result and first divergence
SHA256SUMS
```

Safe instrumentation must be observation-only, isolated from production lineage,
and report its commit separately. Debug synchronization must never be confused with
the production lifecycle result.

## 4. Universal semantic oracles

For every positive case:

1. independently recompute the method-specific `L0/K/H/S/E/V` from immutable
   inputs, not from production helper output;
2. independently gather canonical FullSource rows and compare the complete active
   Window table, including future-column changes and deterministic tail padding;
3. verify device exact, CPU exact and CPU upper carry one generation/epoch and obey
   builder semantics;
4. observe the actual Draft operator table and length; L4 metadata is necessary,
   while L5 kernel/profiler evidence must be separately labeled;
5. recompute physical write slots from full block table + absolute positions and
   prove OFF/ON equality;
6. prove Target metadata identity/content/read lengths and controlled logits are
   unchanged;
7. prove backing cannot be reused before real consumer completion;
8. collect component and end-to-end performance data under the performance plan.

Output equality is supporting evidence only; it cannot substitute for physical
read, slot, Target or lifetime oracles.

## 5. Positive DFlash campaign

Common route: owner-approved DFlash target/draft pair, dense FIA/GQA, one gid,
`METHOD=dflash`, static configured K, Window query width K+1, STANDARD hardware,
single card/TP1 serialized eager, async/prefix/Graph/parallel flags off.

Execution precondition: the owner-signed DFlash target/draft identities described in
§1 are present and their resolved architectures match the intended route. Until
then, every `DFA-*` case is planned but not runnable; do not substitute Eagle3 or a
co-trained V4 checkpoint.

| Case | Goal and request fixture | W / K | Expected plan/table | Special oracle | PASS criteria | Artifact path |
|---|---|---|---|---|---|---|
| DFA-01-SHORT | Prompt whose prepared exact end is `<=W`; generate enough tokens to observe proposals | owner W, K | S=0; V=E; canonical prefix columns | No history is dropped | All universal oracles; OFF/ON deterministic output compatible | `DFA-01-SHORT/` |
| DFA-02-BOUNDARY | Choose tokens so `H-W` is exactly divisible by legacy B | owner W, K | `S=H-W`; exact aligned slice | First/last source columns and valid count | Complete table equals independent slice; operator table/length match | `DFA-02-BOUNDARY/` |
| DFA-03-NONBOUNDARY | `H-W` strictly inside a block | owner W, K | `S=floor((H-W)/B)B`; visible includes alignment slack | No second alignment or W clamp | Independent integer oracle and table match | `DFA-03-NONBOUNDARY/` |
| DFA-04-LONG | Long prompt completed through pure-prefill baseline bypass, then decode | owner W, K | Decode proposal uses bounded Window; prefill creates zero generation | Profile/dummy/pure prefill stays baseline | No mixed row; first decode enters Window; no startup failure | `DFA-04-LONG/` |
| DFA-05-KPLUS1 | Explicitly prove query width K+1 | two K values | CPU upper reflects actual width once; exact remains prepared E | No duplicate step addition | Metadata and FIA carrier use documented exact/upper semantics | `DFA-05-KPLUS1/` |
| DFA-06-REJECTION | Deterministic fixture or bounded seed search producing partial rejection before next proposal | owner W, K | Current proposal state unchanged; next proposal derives new full L0 | No stale prior Window source | All generations map to canonical source; no epoch reuse | `DFA-06-REJECTION/` |
| DFA-07-LIFETIME | A/B/A proposals with forced observation pressure but no semantic change | owner W, K | Stable backing address, mutable contents, increasing generation | Event/stream completion before overwrite | Happens-before proof and no early reuse | `DFA-07-LIFETIME/` |
| DFA-08-PROFILE | Same model/config OFF/ON/A' with profiler | representative W/K | Semantics equal to matching correctness case | D2H/H2D/sync/event/memory attribution | Performance artifacts complete; no contention | `DFA-08-PROFILE/` |

## 6. Positive eligible DSpark campaign

Common route: owner-approved non-DeepSeek-V4 co-trained DSpark pair; all other
constraints equal DFlash.

Execution precondition: the owner-signed DSpark pair from §1 is present. The
`sample_from_anchor` value is read from the **draft model's resolved HF config** by
both upstream and Ascend DSpark constructors; it is not a vLLM CLI option. For
`DSP-02`, use a dedicated immutable owner-approved checkpoint/revision whose
`config.json` resolves to `"sample_from_anchor": false`, archive the before-run
realpath/revision/config hash and effective value, and never edit a shared model in
place. If no such checkpoint is supplied, classify `OWNER_INPUT_MISSING`.

| Case | Goal and request fixture | W / K/query width | Expected plan/table | Special oracle | PASS criteria | Artifact path |
|---|---|---|---|---|---|---|
| DSP-01-K | Default `sample_from_anchor=true` | owner W, K | Actual query width K | Width and upper are K, not inherited DFlash K+1 | Universal oracles | `DSP-01-K/` |
| DSP-02-KPLUS1 | Owner-approved draft HF config explicitly resolves `sample_from_anchor=false` | owner W, K+1 | Same source semantics, different upper/query width | Archive config hash/effective value and distinguish operator q length | Universal oracles; absent checkpoint is `OWNER_INPUT_MISSING`, not FAIL/PASS | `DSP-02-KPLUS1/` |
| DSP-03-BOUNDARY | Exact aligned anchor | owner W/K | Canonical aligned slice | Complete table and operator args | Universal oracles | `DSP-03-BOUNDARY/` |
| DSP-04-NONBOUNDARY-LONG | Long prompt then pure decode, nonaligned anchor | owner W/K | Baseline prefill, Window decode | No mixed batch; no double alignment | Universal oracles | `DSP-04-NONBOUNDARY-LONG/` |
| DSP-05-REJECTION | Partial acceptance/rejection affects next proposal | owner W/K | Each proposal starts from fresh full state | Epoch and source freshness | Universal oracles | `DSP-05-REJECTION/` |
| DSP-06-LIFETIME-PROFILE | A/B/A plus profiler | representative | Stable backing, distinct generations | Event/lifetime and overhead | Universal + performance criteria | `DSP-06-LIFETIME-PROFILE/` |

## 7. Positive Eagle3 static-K campaign

Reference known model identity from old evidence: target Qwen3-4B at
`/mnt/share/z00841464/model_weights/Qwen3-4B`; the draft model absolute path must
be resolved and archived anew. Common route: normalized Eagle3, static K=3 unless
the case says otherwise, dense FIA/GQA, one gid, STANDARD hardware, TP1 serialized
eager, async/prefix/Graph/parallel flags off.

| Case | Goal and request fixture | W / K | Expected S/E/V | Special oracle | PASS criteria | Artifact path |
|---|---|---|---|---|---|---|
| E3-01-SHORT | `H=L0+K<=W` | W=64,K=3 | S=0; E0/E1/E2 from real steps; V=E | First-pass Draft-private metadata | Universal oracles; Target remains untouched | `E3-01-SHORT/` |
| E3-02-BOUNDARY | Choose `H-W` exactly on B boundary | 64/3 or model-valid values | Frozen aligned S across step0/1/2 | `S0=S1=S2` | Full table and operator exact for every step | `E3-02-BOUNDARY/` |
| E3-03-NONBOUNDARY | Choose nonaligned `H-W` | 64/3 | Frozen floor-aligned S; V changes with E | No per-step S recomputation | Universal oracles | `E3-03-NONBOUNDARY/` |
| E3-04-LONG | Long prompt, pure-prefill baseline bypass, then first decode proposal | 64/3 | No Window generation during all-prefill chunks; valid proposal L0 after completion | First-pass classification | No startup/mixed abort; first real proposal uses Window | `E3-04-LONG/` |
| E3-05-FUTURE-COLUMN | `B=16,W=64,K=3,L0=64` where possible, or equivalent real B geometry | as fixture | H=67, S=0; later E enters next physical column | Step1/2 table refreshed from FullSource, not step0 Window | New full column appears exactly when oracle requires | `E3-05-FUTURE-COLUMN/` |
| E3-06-REJECT-SAME-BLOCK | Deterministic rejection within same block | 64/3 | Proposal S remains frozen despite corrected E | Step exact follows kernel semantics | No S drift; lengths/table same generation | `E3-06-REJECT-SAME-BLOCK/` |
| E3-07-REJECT-CROSS-BOUNDARY | Bounded fixture/seed search for rejection crossing frozen anchor/block | 64/3 | Expected fail-closed or valid interval exactly per static contract | Record inability as `INSUFFICIENT_EVIDENCE`, never PASS | Observed result equals independently predicted contract | `E3-07-REJECT-CROSS-BOUNDARY/` |
| E3-08-ABA | Sequential A→B→A' with distinct generations | 64/3 | Same semantic table for A/A' allowed; generation/epoch differ | Stable address does not erase freshness | B cannot contaminate A'; stale A rejected | `E3-08-ABA/` |
| E3-09-ROW-REUSE | Finish request A in persistent row R; admit D into R | 64/3 | New ordered request fingerprint/epoch; fresh FullSource binding | Instrument idx_mapping and row owner | Actual row reuse observed; stale A cannot publish/read | `E3-09-ROW-REUSE/` |
| E3-10-BATCH2-DECODE | Controlled two-request pure-decode batch if constructible without scheduler source change | 64/3 | Independent rows under one generation | Reorder `[A,B]→[B,A]`, finish/add | No mixed row; complete per-row oracle | `E3-10-BATCH2-DECODE/` |
| E3-11-SLOT-TARGET | Dedicated complete untruncated slot/write/Target trace | 64/3 | Read Window differs; write/Target remains full | Independent slot recomputation | Every slot and Target field/logit criterion passes | `E3-11-SLOT-TARGET/` |
| E3-12-LIFETIME | Rapid A/B/A contents with real consumer event | 64/3 | Address stable, overwrite only after completion | Event/stream happens-before | No early reuse; exact event identity per step | `E3-12-LIFETIME/` |
| E3-13-PROFILE | OFF/ON/A' representative short and long cases | 64/3 | Same semantics as correctness fixtures | Component + E2E performance | Meets owner threshold; raw samples complete | `E3-13-PROFILE/` |

## 8. Negative campaign

Each case must prove the intended reason occurs before live FullSource/workspace
allocation and leaves Target/baseline state intact. A resource/import/model error is
`ENVIRONMENT_OR_FIXTURE_ERROR`, not a Gate pass.

| Case | Configuration | Expected state / observation | Required artifact |
|---|---|---|---|
| NEG-01-CONFIG-OFF | Omit `draft_window_size` for Eagle3/DFlash/DSpark/DFlash2/plain Eagle and representative baseline topology | `CONFIG_OFF`; original dispatch; zero Window/P7/Graph provider state | allocation spy + baseline output/config |
| NEG-02-MTP | MTP with valid and invalid numeric W | `FORCED_OFF` before numeric validation; warning-once; zero state | policy/order trace |
| NEG-03-V4-DSPARK | DeepSeek-V4 co-trained DSpark with W | `FORCED_OFF`; zero state | normalized model/method policy trace |
| NEG-04-PLAIN-EAGLE | plain Eagle with W | `OWNER_BLOCKED` product status; configuration-time rejection | exact diagnostic and zero allocation |
| NEG-05-DYNAMIC-K | Eagle3 dynamic speculative decoding | `OWNER_BLOCKED`; reject before proposal state | configured/scheduled K trace + zero allocation |
| NEG-06-DFLASH2 | DFlash2 with W | `FAIL_CLOSED` before live source | route identity + reason |
| NEG-07-DSA | DSA-v1/SAS/QLI/compressor consumer | `FAIL_CLOSED` before live source | actual backend inventory + reason |
| NEG-08-SFA | SFA main/indexer | `FAIL_CLOSED` before live source | both consumer identities + reason |
| NEG-09-MLA | MLA | `FAIL_CLOSED` before live source | builder/backend identity + reason |
| NEG-10-RESIDENT | native SWA/recycling/offload | `FAIL_CLOSED` before live source | layout/resident classification + reason |
| NEG-11-MULTIGROUP-H | homogeneous multiple gids | `FAIL_CLOSED` | group inventory and zero materialization |
| NEG-12-MULTIGROUP-X | heterogeneous groups | `OWNER_BLOCKED` | group signatures and zero materialization |
| NEG-13-PARALLEL | Each §2.1 TP2, DP2, PP2, PCP2 and DCP2 fragment, one case per dimension | `FAIL_CLOSED` for the exact dimension | expanded argv + topology fingerprint + preallocation spy |
| NEG-14-FLAGS | Each §2.1 SP, DSA-CP and FlashComm construction | `FAIL_CLOSED`; SP may report its required TP/DP dimensions in the same exhaustive reason | expanded argv/effective config/environment + reason |
| NEG-15-ASYNC | `--async-scheduling`, otherwise exact candidate | `STATIC_READY`; live materialization rejected before FullSource | expanded argv + capability and allocation trace |
| NEG-16-PREFIX | `--enable-prefix-caching`, otherwise exact candidate | `FAIL_CLOSED` before source | expanded argv + config/fingerprint/reason |
| NEG-17-GRAPH | FULL, FULL_DECODE_ONLY, PIECEWISE separately | `GRAPH_FROZEN`; hard reject; no provider installation | graph mode and allocation/provider trace |
| NEG-18-310P | COMPATIBILITY hardware profile, non-MTP method | P7 Window family rejection before FullSource. The 310P patch delegates non-MTP methods to the baseline factory; this case must not expect a general MTP-only startup rejection. | device profile, baseline startup route, capability reason and zero-allocation trace |
| NEG-19-MIXED | One decode row plus one prefill row | `OWNER_BLOCKED`; current behavior is known EngineCore-risk and must be isolated to a disposable service | exact exception/blast-radius artifact; never a release PASS |

## 9. Result classification

Each oracle is one of `PASS`, `FAIL`, `INSUFFICIENT_EVIDENCE`, or
`ENVIRONMENT_OR_FIXTURE_ERROR`. The case passes only if every mandatory oracle is
PASS; `INSUFFICIENT_EVIDENCE` keeps the associated Gate open. A negative case passes
only on its exact intentional Gate, not merely because the service failed.

## 10. Campaign stop conditions

- Any Target mutation, slot mismatch, Window-of-Window source, stale generation,
  early overwrite, or unsupported silent fallback stops the campaign.
- Any mismatch between runtime imports and pinned SHAs invalidates the run.
- Mixed serving must use a disposable service until owner scope is resolved.
- Graph execution is never enabled by this plan; negative Gate checks only.
- No status advances to `SUPPORTED` until independent review adjudicates all raw
  artifacts and the owner approves the mandatory matrix.

```text
P8 LOCAL OUTPUT: PLAN ONLY
COMPREHENSIVE EAGER NPU CAMPAIGN: NOT STARTED
```
