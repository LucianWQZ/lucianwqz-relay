**# P4b R3 — Final Eagle3 NPU Correctness Validation Report**



\> **\*\*STATUS UPDATE — this report has been resumed.\*\*** The capacity blocker resolved and the

\> campaign was executed on real NPU. See **\*\*§25 Resume Run After Capacity Recovery\*\*** at the

\> end of this document for the executed results and the updated gate verdicts.

\> The original ENVIRONMENT_BLOCKED analysis below is retained unaltered as history.



MRV2 Draft Sliding Window, phase R3.

Final production branch unmodified. No performance. No P5.



Generated: 2026-10-12

Container: \`vllm-wenqing-dev\` (host \`node133\`)

Root: \`/home/wenqing/mrv2_window_test\`



**---**



**## 1. Executive Summary**



\*\*The NPU campaign could not be run. The shared server is fully claimed by another

tenant's workload.\*\*



At the start of the campaign, chip 0 was already occupied by a \~59.7 GiB external job; by

the end, **\*\*all eight chips had \~1.5 GiB free of 64 GiB\*\***. Our route needs \~54.9 GiB at the

verified \`gpu-memory-utilization 0.90\`, and even a drastically reduced 0.25 would need

15.2 GiB. This is not a code or configuration problem: the launch failed inside

\`init_device()\` with



\`\`\`

ValueError: Free memory on device (1.28/60.96 GiB) on startup is less than desired

GPU memory utilization (0.9, 54.86 GiB).

\`\`\`



The tenant's job was *\*growing\** while I polled (12.6 GiB free → 1.5 GiB free over \~3 min), so

waiting is not a short-term fix. I did not touch their workload.



What I did complete, entirely on CPU, so the campaign can run the moment capacity is

available:



\- **\*\*Level 4 instrumentation built and CPU-validated\*\*** — the decisive addition this phase.

  It captures the operand physically bound to the NPU FIA task.

\- **\*\*28/28 trace tests pass\*\***, including the new Level 4 tests.

\- **\*\*7 exact-token fixtures\*\*** built with the real Qwen3-4B tokenizer, including the

  \`H = 192\` exact-boundary case (F03) and a 4-block-span case (F07).



Both gates are therefore **\*\*not\*\*** PASS. \`R3 SEMANTIC CORRECTNESS: BLOCKED\` (cases not

executed) and \`R3 PHYSICAL/LIFECYCLE: OPEN\` (instrument ready, never exercised on NPU).

\`G-AR-STEP\` stays **\*\*OPEN\*\***.



**---**



**## 2. Exact Git / Runtime State**



\| | commit | tree | dirty |

\|---|---|---|---|

\| vLLM (Final) | \`84030bbe3d74d99bad477a3d2e37a973ccd8865c\` | \`f3e320f8…\` | **\*\*0\*\*** |

\| vLLM-Ascend (Final) | \`1011e2c2fa99729a46efde5b5bbaf6daed975a2c\` | \`7d165d585755766e7493e02f0281598e4aca3602\` | **\*\*0\*\*** |

\| Ascend (Debug) | \`30c87a59833c4e0be87daf3a2fa60b6bd7353363\` | — | clean |



Debug commit chain: \`4c79efaa7\` (R3a) → \`11e6369e\` (R3a+) → \`30c87a598\` (R3 Level 4).

Final HEAD and tree verified unchanged before and after the phase. No venv activated.



**---**



**## 3. R3a+ Reference**



Verified before any work:



\`\`\`

debug source  : /home/wenqing/mrv2_window_test/debug-src/p4b-r3         OK

debug overlay : /home/wenqing/mrv2_window_test/runtime-debug-p4b        OK

debug launcher: /home/wenqing/mrv2_window_test/scripts/qwen3_4b_eagle3_p4b_debug.sh  OK

debug commit  : 11e6369e33304b395fc334c12eb9c77939e147eb               (as reported)

native md5    : 354c6331dbaf (vllm_ascend_C) / 3ec413cf7436 (kernels)  (as reported)

\`\`\`



**---**



**## 4. Exact Route**



Target \`Qwen3-4B\`, draft \`eagle3_qwen3_4b\`, method \`normalized Eagle3\`, **\*\*K=3\*\***, **\*\*W=64\*\***,

TP=1, DP/PP/PCP/DCP/SP=1, dense GQA, serialized eager, graph NONE, async false, prefix cache

false, DSA-CP false, FlashComm false, fixed seed.



**\*\*Block size read from runtime inventory, not the B=16 example:\*\***



\`\`\`

"logical_block_size": 128   "kernel_block_size": 128

"block_span_tokens": 128    "legacy_block_size_B": 128    "window_size_W": 64

\`\`\`



**\*\*B = 128\*\*** confirmed.



**---**



**## 5. Campaign Design**



As specified: three service campaigns rather than a restart per case.



\| campaign | mode | status |

\|---|---|---|

\| A1 | Window OFF baseline | **\*\*NOT_RUN\*\*** (ENVIRONMENT_BLOCKED) |

\| B | Window ON W=64 debug | **\*\*NOT_RUN\*\*** (ENVIRONMENT_BLOCKED) |

\| A2 | Window OFF again (drift/leak) | **\*\*NOT_RUN\*\*** (ENVIRONMENT_BLOCKED) |



One launch attempt was made and failed at device init before any model work (see §21). That

attempt is itself the environment evidence; no further launches were attempted because the

precondition (\`free >= gmu × total\`) was provably false.



**---**



**## 6. Prompt Fixtures**



\`debug/fixtures/p4b_correctness_fixtures.json\`, built with the exact Qwen3-4B tokenizer

(\`transformers.AutoTokenizer\` from \`/mnt/share/z00841464/model_weights/Qwen3-4B\`). Token

counts are **\*\*measured\*\***, never inferred from character length.



\| fixture | tokens | H = L0+K | start | visible | case |

\|---|---|---|---|---|---|

\| \`F01_short\` | 9 | 12 | 0 | 9 | SHORT (H ≤ W ⇒ start = 0) |

\| \`F02_tiny\` | 1 | 4 | 0 | 1 | SHORT |

\| **\*\*\`F03_boundary\`\*\*** | **\*\*189\*\*** | **\*\*192\*\*** | **\*\*128\*\*** | **\*\*61\*\*** | **\*\*EXACT_BOUNDARY ((H−W) = 128 = B)\*\*** |

\| \`F04_nonbound_lo\` | 161 | 164 | 0 | 161 | NON_BOUNDARY (0 < H−W < B) |

\| \`F05_nonbound_hi\` | 200 | 203 | 128 | 72 | NON_BOUNDARY (H−W = 139) |

\| \`F06_multistep\` | 300 | 303 | 128 | 172 | NON_BOUNDARY |

\| \`F07_blockcross\` | 600 | 603 | 512 | 88 | NON_BOUNDARY, 4-block span |



Each record holds id, raw text, measured token count, token-ids hash, purpose, predicted

geometry, and (to be filled post-run) observed geometry. F03 lands on \`H = 192\` — the exact

boundary the task predicted.



**---**



**## 7–15. Case Results**



Every case in E01–E12 is **\*\*NOT_RUN\*\*** for want of NPU capacity. No status is invented; in

particular E09 is *\*not\** recorded as PASS.



\| ID | case | expected | actual | evidence level | status |

\|---|---|---|---|---|---|

\| E01 | profile/dummy bypass | no production generation; bypass traced | — | — | **\*\*NOT_RUN\*\*** |

\| E02 | pure prefill baseline | baseline full read; zero window generation | — | — | **\*\*NOT_RUN\*\*** |

\| E03 | short context | \`window_start_abs == 0\` | — | — | **\*\*NOT_RUN\*\*** |

\| E04 | exact boundary (H=192) | \`start = H − W = 128\`; active row = canonical slice | — | — | **\*\*NOT_RUN\*\*** |

\| E05 | non-boundary | \`start = B·floor((H−W)/B)\` | — | — | **\*\*NOT_RUN\*\*** |

\| E06 | multi-step K=3 | complete proposal, frozen anchor across 3 steps | — | — | **\*\*NOT_RUN\*\*** |

\| E07 | future physical block | new column from canonical FullSource | — | — | **\*\*NOT_RUN\*\*** |

\| E08 | rejection same block | anchor not recomputed; real correction | — | — | **\*\*NOT_RUN\*\*** |

\| E09 | rejection cross boundary | — | — | — | **\*\*NOT_RUN\*\*** |

\| E10 | multi-request reorder | no cross-request table/length bleed | — | — | **\*\*NOT_RUN\*\*** |

\| E11 | finish / add / row reuse | stale generation invalidated | — | — | **\*\*NOT_RUN\*\*** |

\| E12 | negative gates | fail-closed before workspace materialise | — | — | **\*\*NOT_RUN\*\*** |



Work already evidenced in **\*\*R3a+\*\*** (single request, short context) and reusable as a

starting point once capacity returns: oracle 0 divergences, 12/12 proposals complete with

\`expected == observed == 3\`, 36/36 active-row equality, write-side carriers recorded. The R3

cases exist to extend that to boundary/non-boundary anchors, multi-request and negative gates

— none of which could be exercised.



**---**



**## 16. FullSource Projection**



Per-row projection verification (\`expected_row = canonical_full_row[start : start+req]\`,

then \`materialized_row == expected_row\`, \`consumer_row == materialized_row\`) is instrumented

and CPU-validated (§17), but **\*\*not executed against a live EngineCore\*\*** this phase.



**---**



**## 17. Frozen Invariants**



A1/B/A2 comparison could not be performed — no campaign ran. The instrumentation that would

capture the required invariants (positions, query_start_loc, slot_mapping, canonical

FullSource, Target metadata owner and active values) exists and passed CPU tests in R3a+.



**---**



**## 18. Physical Operand Evidence**



**### 18.1 What was added**



The consumer → backend → operator chain was traced read-only:



\`\`\`

speculator.\_build_eagle3_private_attn_metadata      [LEVEL 3, R3a+]

  -> build_attn_metadata(...)

attention_v1.AttentionV1Impl.forward_fused_infer_attention

  (eager path: \`if \_EXTRA_CTX.capturing:\` is False -> eager branch)

  -> \_get_fia_params(...)  => block_table, actual_seq_lengths_kv

  -> DeviceOperator.npu_fused_infer_attention_score(block_table=..., actual_seq_lengths_kv=...)

       device/device_op.py:110

       -> torch_npu.npu_fused_infer_attention_score(\*\*kwargs)      <<< THE OPERATOR

\`\`\`



The graph-only sites (\`update_graph_params\`, \`full_graph_pa\`) are **\*\*not\*\*** on our route

(graph NONE), which is why the eager FIA leaf is the correct hook.



**\*\*Instrumented at \`device/device_op.py:110\`\*\*** — the leaf Python frame immediately before the

NPU operator launch. The operand captured there is the operand physically bound to the FIA

task, i.e. **\*\*LEVEL_4_TASK_BOUND_OPERAND\*\***, not a Python-side intermediate.



The instrumentation is gated by the same \`VLLM_ASCEND_DRAFT_WINDOW_DEBUG=1\` check, which

guards *\*both\** the import and the trace, so a disabled run pays one string compare and

nothing else. It only captures after a window consumer boundary has been seen (target-only

FIA calls are not traced) and is bounded by \`...\_MAX_FIA\`. The operator call itself is

byte-identical — the diff is a pure insertion.



**### 18.2 Cross-check design**



\`on_fia_operand\` joins the operator operand against the last window consumer boundary and

records \`matches_last_consumer_boundary\`. A \`True\` means \*\*the operand handed to the NPU

operator is the same window table that was validated at Level 3\*\* — closing the

consumer→operator gap. CPU tests cover match, mismatch, pre-window silence, and the cap.



**### 18.3 Honest status**



**\*\*Level 4 is instrumented and CPU-validated but has never fired on NPU.\*\*** No

\`fia_operator_operand\` record exists from a real run. Level 5 (profiler/kernel) was not

attempted. Per the task's rule, Level 3 is not renamed to Level 4 — the claim is only that

the hook is placed at the operator boundary.



**---**



**## 19. Stream / Lifecycle**



Not executed. The planned core case (full semantic debug, then re-run with

\`MAY_SYNC_DEVICE\` disabled so only \`LOGICAL_ONLY\`/\`NO_DEVICE_SYNC\` events remain, and confirm

no behaviour change or stale state) requires a running service. The trace already supports it

via \`...\_ROW_EQUALITY=0\` plus the per-event \`sync_class\`, and the non-syncing path is

unit-covered, but no NPU evidence exists.



**---**



**## 20. Negative Gates**



Not executed (E12). Note that even these are not trivially runnable while memory is

exhausted: the config gates at \`draft_window\.py:650/654/675\` and

\`draft_window_eagle3.py:104\` are reached around speculator construction, after device

initialisation, so they too would currently fail on the memory precondition first.



**---**



**## 21. Failures / First Divergence**



**\*\*No semantic divergence was observed\*\*** — no case ran far enough to produce one. The single

failure this phase is environmental, and it is the *\*first\** divergence in the strict sense:



\`\`\`

case      : Campaign B, Window ON W=64, card 0, gmu 0.90

expected  : Ynnnnn / engine reaches "Application startup complete"

actual    : startup: 0 ready, 38 errors; request FAILED

root cause: ValueError: Free memory on device (1.28/60.96 GiB) on startup is less than

            desired GPU memory utilization (0.9, 54.86 GiB)

            at  vllm/v1/worker/.../init_device()  (via EngineCore.\_\_init\_\_)

layer     : environment / device acquisition — NOT window, NOT route, NOT instrumentation

trace     : no trace records emitted (engine never reached the window code)

suspected : none in our code

evidence  : npu-smi HBM per chip, before and during

static    : no static test could have caught this; it is a runtime resource condition

\`\`\`



Per §12 this is classified \`ENVIRONMENT_BLOCKED\`, not a code defect. No

\`First_Divergence_Report.md\` was raised as a semantic divergence, because there is no

semantic divergence to report.



**---**



**## 22. Raw Artifact Index**



\`\`\`

debug/p4b_r3_plus.patch                     Level 4 + R3a+ instrumentation (4 files, +674/-1)

debug/debug_commit_v3.txt                   commit 30c87a59833c4e0be87daf3a2fa60b6bd7353363

debug/test_p4b_r3a_plus_trace.py            28 tests (CPU), incl. 5 Level-4 tests

debug/fixtures/p4b_correctness_fixtures.json  7 tokenizer-exact fixtures

debug/make_p4b_fixtures.py                  fixture generator

debug/trace_schema_v2.md                    field-source table, oracle, sync classes

debug/selected_trace_v2.jsonl / .log        R3a+ live ON trace (198 records) + rendering

reports/P4b_R3a_Observability_Report.md

reports/P4b_R3a_Plus_Trace_Semantics_Report.md

reports/P4b_R3_Final_Correctness_Report.md   this report

logs/qwen3_4b_eagle3_p4b_debug_on.log       the blocked launch log (38 errors)

\`\`\`



**---**



**## 23. Gate Table**



\| gate | requirement | status |

\|---|---|---|

\| Semantic — oracle correct | 0 divergences | ✅ (R3a+, single request) |

\| Semantic — proposal complete | expected == observed | ✅ (R3a+, 12/12) |

\| Semantic — window anchor correct | start = B·floor((H−W)/B) | ✅ short-context only; **\*\*boundary/non-boundary NOT_RUN\*\*** |

\| Semantic — per-step exact correct | E_s independent oracle | ✅ (R3a+, 36/36) |

\| Semantic — FullSource projection | row slice equality | ✅ (R3a+, 36/36) |

\| Semantic — Target/write-side invariant | unchanged across A/B/A | **\*\*NOT_RUN\*\*** |

\| Semantic — multi-request clean | no cross-request bleed | **\*\*NOT_RUN\*\*** |

\| Physical — task operand | operand == oracle table | instrument ready, **\*\*never fired on NPU\*\*** |

\| Physical — stream/lifecycle | no early overwrite under real stream | **\*\*NOT_RUN\*\*** |

\| Negative gates | fail-closed before materialise | **\*\*NOT_RUN\*\*** |



**---**



**## 24. Final Verdict**



**# \`R3 SEMANTIC CORRECTNESS: BLOCKED\`**



Reason: the R3 campaign could not execute. This is not a correctness failure — it is

absence of execution. The subset already established in R3a+ (oracle, proposal

completeness, per-step exact, FullSource projection, active-row equality, all on a single

short-context request) is unaffected and remains valid, but the R3 gate additionally

requires boundary/non-boundary anchors, multi-request isolation, Target/write invariants

across A/B/A, and negative gates, none of which ran.



**# \`R3 PHYSICAL/LIFECYCLE: OPEN\`**



Level 4 instrumentation is built and CPU-validated but has never produced a live record;

Level 5 was not attempted. Real-stream lifecycle was not exercised.



**# \`G-AR-STEP: OPEN\`**



Not closed. Both required gates must pass for closure.



Closure would additionally require listing Target, Draft, K, W, B, backend, TP,

eager/graph/async/prefix, Final commit, Debug commit, and the highest evidence level — that

list is prepared in §4 and §18.1 and can be emitted verbatim once the gates pass.



**\*\*Not claimed:\*\*** P4b correctness, physical read-set equivalence, any G-gate closure,

performance, or release readiness.



**---**



**## Resume Procedure (for when NPU capacity returns)**



\`\`\`bash

\# 1. precondition

timeout 25 npu-smi info | grep -oE '[0-9]+/ \*65536'   # need free >= 54864 MB at gmu 0.90

\# 2. rebuild the debug overlay (it is a copy; source edits require this)

bash /home/wenqing/mrv2_window_test/scripts/build_p4_runtime_overlay_debug.sh

\# 3. Campaign A1 (OFF) / B (ON) / A2 (OFF) with the tokenizer-exact fixtures

\#    fixture prompts live in debug/fixtures/p4b_correctness_fixtures.json

\# 4. ON trace: VLLM_ASCEND_DRAFT_WINDOW_DEBUG=1, ...\_MAX_STEPS>=3, ...\_MAX_FIA>=8

\# 5. join fia_operator_operand.matches_last_consumer_boundary against oracle values

\`\`\`



A reduced \`gpu-memory-utilization\` would be an undocumented deviation from the verified

route and should be authorised explicitly before use; it would not have helped this phase

anyway (15.2 GiB needed at 0.25 vs 1.5 GiB free).



Stopped. No performance run. No P5. Final production branch untouched.





**---**



**# 25. Resume Run After Capacity Recovery**



The blocker in §1 resolved on its own — the external tenant's job finished. \*\*No process of

another tenant was killed at any point.\*\* The resume ran the campaign on real NPU.



**## 25.1 Capacity recovery**



\`\`\`

NPU processes : none on any chip

HBM           : \~3.4 GiB used / 62.1 GiB free per chip   (3.4 GiB = CANN baseline)

AICore        : 0% (idle), Health OK on all 8

\`\`\`



Capacity Gate: card 0, 62,115 MB free vs 54,864 MB required at \`gmu=0.90\` → **\*\*PASS\*\***.

At the very end of the phase an 8-card external job returned; its PIDs are \*\*not in this

container's PID namespace\*\*, confirming it belongs to another tenant and was left alone.



**## 25.2 Debug commit progression**



\`\`\`

4c79efaa7 (R3a)  ->  11e6369e (R3a+)  ->  30c87a598 (R3 Level 4)  ->  6e06c5486 (resume)

\`\`\`



Two further instrumentation-only fixes were required during the resume, both found by running:



1\. **\*\*\`actual_seq_lengths_kv\` is a plain python list upstream\*\*** — the tensor-only

   \`digest()\`/\`as_list()\` raised \`AttributeError("'list' object has no attribute 'detach'")\`

   and silently lost the exact read length at the Level-4 boundary. Helpers now accept

   tensors, ndarrays, lists and tuples.

2\. **\*\*\`NO_SYNC\` mode added\*\*** (\`VLLM_ASCEND_DRAFT_WINDOW_DEBUG_NO_SYNC=1\`): \`digest()\`,

   \`as_list()\` and \`on_fia_operand()\` short-circuit so the trace performs \*\*no device read at

   all\*\*, enabling the stream/lifecycle case without the observation perturbing stream timing.



Final diff vs base: 4 files, **\*\*+713 / −1\*\*** (the single deletion is a local-variable

introduction). Tests: **\*\*33/33 pass\*\***. Final production branch clean throughout.



**## 25.3 Campaigns executed**



\| campaign | mode | fixtures | trace records | provenance verified |

\|---|---|---|---|---|

\| A1 | OFF | 7 | **\*\*0\*\*** | SHA/tree/md5/cmdline |

\| B | ON W=64 | 7 | **\*\*4974\*\*** | ✓ |

\| A2 | OFF again | 3 | **\*\*0\*\*** | ✓ |

\| B2 | ON W=64 (boundary) | 3 (incl. F08) | 1671 | ✓ |

\| B3 | ON W=64 **\*\*NO_SYNC\*\*** | 2 | 1931 | ✓ |

\| A3 | OFF (F08 reference) | 2 | **\*\*0\*\*** | ✓ |

\| E12 | negative gates | 4 attempted | — | **\*\*ENVIRONMENT_BLOCKED\*\*** |



Watertight provenance per campaign: python, \`vllm.\_\_file\_\_\`, \`vllm_ascend.\_\_file\_\_\`,

\`vllm_ascend_C.\_\_file\_\_\`, both Final SHAs+tree, debug SHA, native md5

(\`354c6331dbaf…\` / \`3ec413cf7436…\`), the exact expanded \`vllm serve\` command, and

npu-smi before/after. All under \`results/\<campaign>/\`.



**## 25.4 Semantic results (Campaign B, 4974 records)**



\`\`\`

ORACLE            0 divergences      28/28 proposal rows, 852/852 step rows oracle_match=True

PROPOSALS         284/284 complete   trace_truncated=False, expected==observed==3, all retire

ACTIVE-ROW EQ     852/852 all_rows_equal=True

ERRORS            trace_error 0      abort 0

\`\`\`



**\*\*The single strongest end-to-end signal:\*\*** with \`temperature 0\` and fixed seed, the Window

is **\*\*output-neutral\*\***:



\`\`\`

OFF == ON (byte-identical output)

  F01 F02 F03 F04 F05 F06 F07          all True   (A1 vs B)

  F01 F08                              all True   (A3 vs B2 full-debug AND vs B3 nosync)

OFF == OFF (drift)

  F01 F03 F06                          all True   (A1 vs A2)

\`\`\`



If the window read projection were not exact, the read KV would differ and the greedy decode

would diverge. It does not, on any fixture, on any run.



**## 25.5 Level 4 — task-bound operand, live on NPU**



\`\`\`

fia_operator_operand captured : 400

  DRAFT  (window table [1,2]) : 33   matches_last_consumer_boundary = True : 33/33

  TARGET (full table [1,128]) : 367  matches_last_consumer_boundary = True : 0/367

\`\`\`



\`\`\`

bt=[1,0] shape=[1,2] int32 | kv=[13] q=[4] block_size=128 layout=TND

matches_consumer=True | sha=3da89ee273be1343

epoch=0: step0 kv=[13]   step1 kv=[11]   step2 kv=[12]   <- read length varies per step,

                                                            block table constant

\`\`\`



Two closures:



1\. **\*\*\`block_table\` at the operator == the window table validated at Level 3\*\*** — sha

   \`3da89ee273be1343\`, identical to the R3a+ window-table hash.

2\. **\*\*\`actual_seq_lengths_kv\` at the operator == \`window_visible_exact\`\*\***: **\*\*33/33\*\***

   (\`== window_visible_upper\`: 0/33). The exact read length bound to the FIA task is the

   oracle-validated window visible length.



The 367 target calls correctly do **\*\*not\*\*** match the window table. Level 4 is no longer

"instrumented but unexercised" — it produced 400 live operands.



**## 25.6 Stream / lifecycle (B3, NO_SYNC)**



\`\`\`

fia_operator_operand            : 0     (suppressed — no device read)

digest skipped markers          : 276

oracle divergences              : 0

proposals complete              : 92/92

aborts                          : 0

output vs OFF / vs full-debug ON: byte-identical

\`\`\`



With the trace performing **\*\*no device read\*\***, behaviour is unchanged: same output, no stale

state, no NPU error, 92/92 proposals complete. Unit test

\`test_no_sync_mode_performs_no_device_read\` asserts \`Tensor.cpu\` call count is 0 in this mode.



**\*\*What this does and does not prove.\*\*** It proves the observation is not what makes the run

correct — the run is correct with the observation removed. It does **\*\*not\*\*** prove "no early

workspace overwrite under a real stream": that needs stream/event instrumentation showing

\`previous reader complete -> retire -> rewrite permitted\`, which was not built. These are kept

separate per the task's instruction.



**## 25.7 Case matrix — updated**



\| ID | case | expected | actual | evidence | status |

\|---|---|---|---|---|---|

\| E01 | profile/dummy | no production generation at profile | 0 window records during startup; \`window_initialized\` fires once after | L3 | **\*\*PASS\*\*** |

\| E02 | pure prefill | zero Window generation | OFF with DEBUG=1: **\*\*0 records\*\***; prefill served | L3 | **\*\*PASS\*\*** |

\| E03 | short context | \`start == 0\` (H ≤ W) | F01 L0=13 H=16 start=**\*\*0\*\***; F02 L0=5 H=8 start=**\*\*0\*\*** | L4 | **\*\*PASS\*\*** |

\| E04 | exact boundary | \`start = H − W = 128\` | F08 L0=189 H=192 H−W=**\*\*128\*\*** start=**\*\*128\*\*** oracle_match | L4 | **\*\*PASS\*\*** |

\| E05 | non-boundary | \`start = B·floor((H−W)/B)\` | F04 start=0 (H−W=104); F05 start=128 (H−W=143); F07 start=512 (H−W=543) | L4 | **\*\*PASS\*\*** |

\| E06 | multi-step K=3 | frozen anchor, 3 steps | 284/284 complete \`exp==obs==3\`; L0/H/start fixed per proposal; E_s varies 13/11/12 | L4 | **\*\*PASS\*\*** |

\| E07 | future physical block | new column from canonical full | F07 4-block span, start=512, active rows from canonical slice | L4 | **\*\*PASS\*\*** |

\| E08 | rejection same block | anchor not recomputed | within-epoch \`current_full_end_abs\` varies (13/11/12) with **\*\*constant\*\*** \`window_start_abs\` and constant window table sha | L4 | **\*\*PASS\*\*** |

\| E09 | rejection cross boundary | — | not deterministically inducible from a fixed fixture/seed pair | — | **\*\*INSUFFICIENT_EVIDENCE\*\*** |

\| E10 | multi-request reorder | no cross-request bleed | only single-request fixtures were driven | — | **\*\*NOT_RUN\*\*** |

\| E11 | finish / add / row reuse | stale generation invalidated | not driven | — | **\*\*NOT_RUN\*\*** |

\| E12 | negative gates | fail-closed before materialise | **\*\*attempts invalid — see 25.10\*\*** | — | **\*\*ENVIRONMENT_BLOCKED\*\*** |



**## 25.8 Frozen invariants**



Directly verified from the ON trace:



\| invariant | result |

\|---|---|

\| query layout (\`write_query_start_loc\`) | **\*\*2 distinct values only\*\***: \`[0,4]\` × 284 (proposal) and \`[0,1]\` × 568 (decode) — clean, phase-exact |

\| consumer block-table shape | \`[[1,2]]\` for **\*\*all 852\*\*** boundaries — always the narrowed window view |

\| exact / upper carriers | present on 852/852 boundaries |

\| canonical FullSource table | \`[64,128]\` sha \`a0b2c8c8195b9fe3\`, distinct from the window view |



**\*\*Incomplete:\*\*** \`write_positions\` (495 distinct) and \`write_slot_mappings\` (489 distinct) were

hashed over the **\*\*whole 10240-wide buffer including the inactive tail\*\***, not the active slice.

Per the task's rule ("若使用hash：必须记录 active slice") this is a **\*\*measurement gap\*\*** — those

two invariants are **\*\*not\*\*** claimed. The indirect evidence (byte-identical OFF/ON output on 9

fixture-runs) is strong but is not a substitute.



**## 25.9 Physical operand evidence — levels**



\| level | status |

\|---|---|

\| L1 PLANNER_ONLY | passed |

\| L2 MATERIALIZED_METADATA | passed |

\| L3 LAST_PYTHON_OPERATOR_ARGUMENT | passed |

\| **\*\*L4 TASK_BOUND_OPERAND\*\*** | **\*\*ACHIEVED — 400 live operands, 33/33 draft matching oracle\*\*** |

\| L5 PROFILER/KERNEL | not attempted |



Level 3 was not renamed into Level 4; the Level-4 claim rests on operands captured at

\`device/device_op.py:110\`, the last Python frame before the NPU operator launch.



**## 25.10 E12 negative gates — why BLOCKED**



Four variants were attempted and **\*\*all four results are invalid\*\***. The script classified any

\`ValueError\` as "REJECTED", but every observed error was the **\*\*memory precondition\*\***:



\`\`\`

ValueError: Free memory on device (1.42/60.96 GiB) on startup is less than desired

GPU memory utilization (0.9, 54.86 GiB).

ValueError: No available memory for the cache blocks.

\`\`\`



An external 8-card job had re-taken the server before the gate run. So these are **\*\*not\*\*** P2

gate rejections and are **\*\*not\*\*** reported as such. Two further variants were not runnable at

all: \`dynamic_K\` has no supported CLI surface on this build, and \`mixed_prefill_decode\`

requires a request mix rather than a launch flag.



A correct re-run needs (a) a free card and (b) a classifier that excludes the memory

precondition from "gate rejection".



**## 25.11 Operator/logic defects found during the resume**



1\. **\*\*Campaign driver, twice.\*\*** (a) it polled \`$ROOT/logs/\` while the launcher writes

   \`/home/wenqing/logs/\`; (b) it polled a launch-time snapshot instead of the live log. Both

   fixed.

2\. **\*\*PID capture.\*\*** \`cd /tmp && vllm … &\` backgrounds the whole AND-list, so \`$!\` was the

   subshell PID; the service survived the kill and squatted a port, making three earlier gate

   results look like rejections. Fixed.

3\. **\*\*List operands.\*\*** See 25.2.

4\. **\*\*Fixture offset.\*\*** vLLM's served prompt is **\*\*+4 tokens\*\*** vs the tokenizer-only count, so

   the original F03 (tokenizer 189) served at L0=193 and **\*\*missed\*\*** the boundary. Corrected

   fixture F08 (tokenizer 185) serves at L0=189 → H=192 → H−W=128. \*\*This is exactly why the

   task said to iterate fixtures against real trace values.\*\*



None of these touched production logic.



**## 25.12 Updated verdicts**



**# \`R3 SEMANTIC CORRECTNESS: BLOCKED\`**



Six of the seven required criteria are met with live-NPU evidence: oracle correct (0

divergences across 28 proposals / 852 steps), proposals complete (284/284), window anchor

correct including the **\*\*exact boundary\*\*** (E04 \`start = H−W = 128\`) and non-boundary (E05),

per-step exact correct, FullSource projection correct (852/852 active-row equality), and

Target/write-side unchanged (byte-identical OFF/ON output on 9 fixture-runs).



It is not PASS because two required items are outstanding:

**\*\*E10/E11 multi-request isolation: NOT_RUN\*\*** (only single-request fixtures were driven), and

the **\*\*positions / slot_mapping invariant check is incomplete\*\*** (whole-buffer hashing, 25.8).



**# \`R3 PHYSICAL/LIFECYCLE: OPEN\`**



Level 4 task-bound operand evidence is **\*\*achieved\*\*** (33/33 draft operands match the oracle

window table and the exact read length). The lifecycle half is not: real-stream

no-early-overwrite was not instrumented. The NO_SYNC run shows the result is not

observation-dependent, but that is a different claim and is recorded separately.



**# \`G-AR-STEP: OPEN\`**



Not closed — both gates must pass.



**\*\*Not claimed:\*\*** P4b correctness PASS, G-AR-STEP closure, physical read-set equivalence,

performance, release readiness.



**## 25.13 Raw artifact index (resume)**



\`\`\`

results/A1_off/   A2_off/   A3_off_F08/   B_on/   B2_boundary/   B3_nosync/   E12_negative/

  each: cmdline, provenance.txt, service.log, trace.jsonl, results.json, npu_before/after.txt

debug/run_campaign.sh, drive_fixtures.py, run_negative_gates.sh

debug/fixtures/p4b_correctness_fixtures.json     (7 + F08 corrected boundary)

debug/selected_trace_level4.jsonl                (B trace, 4974 records)

debug/p4b_r3_resume.patch, debug_commit_resume.txt  (commit 6e06c54860d93351f2bc8ab3f4ddae6527c50423)

\`\`\`



**## 25.14 To finish**



1\. **\*\*E10/E11\*\*** — drive 2+ concurrent requests with explicit \`REQ_IDS\`, exercise \`[A,B] -> [B,A]\`

   and finish/add row reuse, re-checking per-request proposal completeness.

2\. **\*\*positions / slot_mapping invariant\*\*** — re-emit with the **\*\*active slice\*\*** (not the whole

   buffer) and compare across A/B/A.

3\. **\*\*E12\*\*** — rerun on a free card with a classifier that excludes the memory precondition.

4\. **\*\*E09\*\*** — search more fixtures/seeds for a cross-boundary rejection, else record

   INSUFFICIENT_EVIDENCE permanently.

5\. **\*\*Stream/lifecycle\*\*** — instrument event/stream completion to evidence

   \`previous reader complete -> retire -> rewrite permitted\`.



Stopped. No performance run. No P5. Final production branch untouched.





**---**



**# 26. Resume Run 2 — E10/E11/E12 and the write-side invariant**



Capacity recovered again (8/8 idle, \~62.1 GiB free per chip). This run filled the cases that

were still NOT_RUN after §25. Nothing already established was re-run.



**## 26.1 Debug commit progression**



\`\`\`

4c79efaa7 -> 11e6369e3 -> 30c87a598 -> 6e06c5486 -> 24758c5f5d835f52d01ef572c566fb36798f0029

\`\`\`



Two more instrumentation defects, both found by running (not by reading):



1\. **\*\*\`admit_step\` recorded REJECTED steps as admitted.\*\*** A step suppressed by the rate limit

   was still added to \`admitted\`, so re-admitting it returned \`True\` — telling the caller a

   step had been captured when it never was. Now only actually-traced steps are recorded.

2\. **\*\*Write-side carriers were hashed as whole buffers.\*\*** \`positions\` and \`slot_mappings\` were

   digested over the full 10240-wide buffer including the inactive tail. \`consumer_boundary\`

   now also emits \`write_positions_active\` / \`write_slot_mappings_active\` with the explicit

   \`slice\` recorded, per the §9 rule.



Also fixed in the **\*\*test tooling\*\*** (not the repo): the older \`test_p4b_r3_trace.py\` encoded v1

rate-limit semantics; updated to v2 (per-proposal, idempotent). Suite is now \*\*44 tests

(36 + 8), all passing\*\*.



**## 26.2 E10 / E11 — ROUTE_BLOCKED**



Three independent approaches to batch>1 were attempted; \*\*all three are closed by the route

or by the API\*\*, and one of them produced a hard EngineCore abort.



\| # | approach | outcome |

\|---|---|---|

\| 1 | two concurrent HTTP requests, short + long prompt | **\*\*EngineCore death\*\*** — mixed prefill/decode |

\| 2 | two concurrent, barrier-synchronized, identical token length | **\*\*EngineCore death again\*\*** — still separate scheduler steps |

\| 3 | \`n=2\` (two sequences of one prompt ⇒ same step) | HTTP **\*\*400\*\***: \`"n must be 1 when using greedy sampling, got 2."\` |



Approach 3's rejection is a plain vLLM API constraint (greedy ⇒ n=1), not a window gate; the

route requires \`temperature=0\` + fixed seed, so it cannot be worked around without breaking

determinism.



Approaches 1 and 2 failed identically and the root cause is unambiguous:



\`\`\`

NotImplementedError: MRV2 draft-window P4a does not support mixed prefill/decode proposals

  draft_window_eager.py:574  \_requires_prefill_baseline_bypass

  <- draft_window_eagle3.py:158 \_eagle3_draft_window_proposal_scope

\`\`\`



**\*\*Substantive finding: this fail-closed route cannot serve concurrent requests.\*\*** Any

arrival that is not in the same scheduler step makes one request prefill while another

decodes, producing a mixed batch, which is fail-closed — and the fail-closed action is a

**\*\*hard EngineCore abort\*\***, not a graceful per-request rejection: both requests fail and the

service stops serving (\`EngineDeadError\`, then connection refused). That is the documented

"mixed仍fail closed" contract, but the blast radius is service-wide and worth flagging

operationally.



E10 and E11 are therefore recorded **\*\*ROUTE_BLOCKED / INSUFFICIENT_EVIDENCE\*\***, not PASS. The

per-request isolation that E10 was meant to demonstrate (each request reading its own

FullSource row, no table/length bleed) **\*\*remains unverified\*\***.



**## 26.3 E12 — negative gates, now measured with a correct classifier**



The §25 attempts were invalid because the classifier treated any \`ValueError\` as a gate

rejection while the real error was the memory precondition. The classifier now distinguishes

**\*\*resource precondition\*\*** from **\*\*gate rejection\*\***, and the graph variant no longer passes

\`--enforce-eager\` (which had been overriding the compilation config, so that variant was

testing nothing).



\| variant | verdict | explicit reason |

\|---|---|---|

\| graph \`FULL_AND_PIECEWISE\` | **\*\*EXPECTED_GATE\*\*** | \`reason=Graph mode FULL_AND_PIECEWISE is not verified in P2\` |

\| async true | **\*\*EXPECTED_GATE\*\*** | \`reason=Async scheduling is not verified in P2\` |

\| prefix cache true | **\*\*EXPECTED_GATE\*\*** | \`reason=prefix cache is not verified for Window ON\` |

\| TP = 2 | **\*\*EXPECTED_GATE\*\*** | \`reason=TP=2 is not verified in P2\` |

\| mixed prefill/decode | **\*\*EXPECTED_GATE\*\*** | \`NotImplementedError: MRV2 draft-window P4a does not support mixed prefill/decode proposals\` |

\| dynamic K | **\*\*NOT_RUN\*\*** | no supported CLI surface on this build |



All five fire as \`MRV2 draft-window capability rejected: method=eagle3 model=qwen3

route=eagle3; …\` — the P2 capability gate, **\*\*before\*\*** any window materialise or forward. E12

is now largely PASS, with \`dynamic_K\` the only untested variant.



**## 26.4 §9 write-side invariant — what is and is not verified**



Fresh ON run (3 fixtures, 390 consumer boundaries) with the active-slice instrumentation:



\| carrier | distinct values | reading |

\|---|---|---|

\| \`write_query_start_loc\` | **\*\*2\*\*** over 390 | cleanly invariant: \`[0,4]\` × 130 (proposal), \`[0,1]\` × 260 (decode) |

\| \`write_slot_mappings_active\` | 273 over 390 | **\*\*varies per step\*\*** (shape \`[0:4]\` proposal, \`[0:1]\` decode) |

\| \`write_positions_active\` | 309 over 390 | **\*\*varies per step\*\*** |



**\*\*Two honest conclusions, one of which corrects the §25 framing:\*\***



1\. \`positions\` and \`slot_mappings\` are **\*\*per-step inputs, not frozen state\*\*** — they must

   change as decoding advances. "Invariant" for them can only mean \*equal between OFF and ON

   at the same step\*, never *\*constant within a run\**.

2\. **\*\*That comparison is structurally unavailable\*\***: with the Window OFF, \`consumer_boundary\`

   is never emitted at all (the window path is what produces it), so A1/A2 contribute **\*\*zero\*\***

   carrier records. An A1/B/A2 carrier comparison therefore cannot be constructed with this

   instrumentation without adding a target-side hook.



What *\*is\** verified: the query layout is invariant; the window read table is constant within a

proposal (\`3da89ee273be1343\`) and narrowed (\`[1,2]\`) against the canonical \`[64,128]\`; and

OFF≡ON byte-identical output on **\*\*12 fixture-runs\*\*** bounds the write side indirectly (a

changed write set would move the logits). The direct carrier comparison is **\*\*not claimed\*\***.



**## 26.5 Updated case matrix**



\| ID | case | status | note |

\|---|---|---|---|

\| E01 | profile/dummy | **\*\*PASS\*\*** | startup clean; \`window_initialized\` once, after profile |

\| E02 | pure prefill | **\*\*PASS\*\*** | OFF+DEBUG=1 → 0 records |

\| E03 | short context | **\*\*PASS\*\*** | \`start=0\` |

\| E04 | exact boundary | **\*\*PASS\*\*** | F08 \`L0=189 H=192 H−W=128 start=128\` |

\| E05 | non-boundary | **\*\*PASS\*\*** | \`start=0\` (H−W=104) and \`start=128\` (H−W=143) |

\| E06 | multi-step K=3 | **\*\*PASS\*\*** | 284/284 complete, \`exp==obs==3\` |

\| E07 | future physical block | **\*\*PASS\*\*** | F07 4-block span, \`start=512\` |

\| E08 | rejection same block | **\*\*PASS\*\*** | anchor constant, \`E_s\` varies 13/11/12 |

\| E09 | rejection cross boundary | **\*\*INSUFFICIENT_EVIDENCE\*\*** | not deterministically inducible |

\| E10 | multi-request reorder | **\*\*ROUTE_BLOCKED\*\*** | 3 approaches closed; mixed-batch fail-closed |

\| E11 | finish / add / row reuse | **\*\*ROUTE_BLOCKED\*\*** | same cause; C cannot arrive while A decodes |

\| E12 | negative gates | **\*\*PASS\*\*** (5/6) | all five explicit \`reason=\` rejections; \`dynamic_K\` NOT_RUN |



**## 26.6 Updated verdicts**



**# \`R3 SEMANTIC CORRECTNESS: BLOCKED\`**



Unchanged from §25 in substance, with E12 now resolved rather than blocked. Still BLOCKED on:

**\*\*E10/E11 multi-request isolation — ROUTE_BLOCKED\*\***, and the \*\*direct write-side carrier

comparison — structurally unavailable\*\* (§26.4). All other required criteria are met with

live-NPU evidence.



**# \`R3 PHYSICAL/LIFECYCLE: OPEN\`**



Level 4 task-bound operand evidence stands (400 operands, 33/33 draft matching the oracle).

Real-stream no-early-overwrite remains unproven.



**# \`G-AR-STEP: OPEN\`**



Both gates must pass; neither does.



**\*\*Not claimed:\*\*** P4b correctness PASS, G-AR-STEP closure, physical read-set equivalence,

multi-request isolation, performance, release readiness.



**## 26.7 Artifacts added**



\`\`\`

results/E12_negative/{graph_FULL_AND_PIECEWISE,async_true,prefix_cache_true,tp2}.log + .cmdline

results/E12_graph/graph.log                     graph gate re-run without --enforce-eager

results/E10_n2/, results/E10_E11_multireq/      multi-request attempts (engine-death evidence)

results/E10_probe/                              n=1 / n=2 API probe

results/B4_active_slice/                        ON run with active-slice carriers (390 boundaries)

debug/run_multireq.sh, debug/drive_multirequest.py

\`\`\`
