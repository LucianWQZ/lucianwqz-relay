**# P4b R3 Closeout Report — node133**



MRV2 Draft Sliding Window — controlled batch, write isolation and lifetime evidence.



Source: \`80.48.37.146\` / \`node133\`, container \`vllm-wenqing-dev\`.

Date: 2026-10-13. Reuses prior evidence; only fills gaps. No Final business logic changed,

no upstream vLLM changed, no P5.



**---**



**## 1. Real version and run identity**



Read from Git, not assumed:



\| | HEAD | tree | status |

\|---|---|---|---|

\| Final vLLM | \`84030bbe3d74d99bad477a3d2e37a973ccd8865c\` | \`f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee\` | clean |

\| Final Ascend | \`1011e2c2fa99729a46efde5b5bbaf6daed975a2c\` | \`7d165d585755766e7493e02f0281598e4aca3602\` | clean |

\| Debug | \`2a4856134648c068cab044ddfb11eb0e0d907453\` | \`…\` | clean |



Debug chain (strictly linear, no force/rebase/amend):



\`\`\`

1011e2c2f -> 4c79efaa7 -> 11e6369e3 -> 30c87a598 -> 6e06c5486 -> 24758c5f5 -> 2a4856134

\`\`\`



\`0144c46\` (the Node101 debug lineage) is **\*\*not present\*\*** anywhere in this repo — verified with

\`git cat-file\`. Nothing was merged or copied over the source machine; **\*\*no action was needed\*\***,

so none was taken.



Debug changes this round were observation/test tooling only, each committed, each followed by

an overlay rebuild, and the loaded files were diffed against the debug worktree.



**## 2. Report corrections (over-claims in §25/§26, carried forward and fixed)**



1\. \*\*Two HTTP attempts hitting the mixed gate do not prove pure-decode multi-request is

   impossible in general.\*\* Corrected: this round added two *\*further\** constructions (offline

   \`enqueue\`, and a token-budget correction) and still could not form the target batch. The

   honest statement is a **\*\*route-level blocker on this build\*\***, not a proof of impossibility.

2\. \*\*\`n=2\` gives HTTP 400 \`"n must be 1 when using greedy sampling"\` — that is a vLLM API

   constraint, not a Window gate.\*\* Corrected; it was reported under E12 in §26.3 and is

   moved out of the negative-gate set.

3\. **\*\*\`positions\` / \`slot_mappings\` changing every step is normal.\*\*** They are per-step inputs,

   not frozen state. "Invariant" for them can only mean \*equal between OFF and ON at the same

   step\*.

4\. \*\*Byte-identical OFF/ON output does not independently prove KV write positions are

   correct.\*\* It bounds the write side; it is not a substitute for a slot oracle.

5\. **\*\*400 \`fia_operator_operand\` records ≠ 400 Draft coverage.\*\*** The count includes Target

   calls. Draft vs Target is separated by table shape and counted explicitly (§7).

6\. **\*\*The mixed rejection is a runtime phase check, not a startup P2 check.\*\*** Corrected

   throughout; only graph/async/prefix/TP2 are start-up P2 capability rejections.

7\. **\*\*A future-column claim needs a real inter-step column demand change\*\***, not merely a long

   prompt spanning many historical blocks.

8\. \*\*OFF producing no Window trace does not by itself prove ON's prefill created no Window

   state.\*\* The prefill-bypass evidence is the ON-side bypass in §6.



Preserved unchanged as a real usability limit:



\`\`\`

EXPECTED_UNSUPPORTED_MIXED_WITH_ENGINE_ABORT

\`\`\`



Recorded as a **\*\*real availability limitation\*\***, never as "the negative test passed, so there

is no risk".



**## 3. Case ledger**



Full machine-readable ledger: \`results/case_results.json\` (28 cases).

Index and run inventory: \`results/run_manifest.json\` (17 run directories).



\| ID | case | status | evidence |

\|---|---|---|---|

\| E01 | profile/dummy bypass | **\*\*PASS_LIVE\*\*** | startup clean; \`window_initialized\` fires once *\*after\** profile; 0 window records during it |

\| E02 | pure prefill baseline | **\*\*PASS_LIVE\*\*** | OFF + DEBUG=1 → 0 records |

\| E03 | short context | **\*\*PASS_LIVE\*\*** | F01 \`L0=13 H=16 start=0\` |

\| E04 | exact boundary | **\*\*PASS_LIVE\*\*** | F08 \`L0=189 H=192 H−W=128 start=128\` |

\| E05 | non-boundary | **\*\*PASS_LIVE\*\*** | \`start=0\` (H−W=104), \`start=128\` (H−W=143), \`start=512\` (H−W=543) |

\| E06 | multi-step K=3 | **\*\*PASS_LIVE\*\*** | 284/284 complete, \`exp==obs==3\`, anchor frozen |

\| E07 | future physical block | **\*\*PASS_LIVE\*\*** | F07 \`start=512\`, 4-block span; active rows == canonical slice |

\| E08 | rejection same block | **\*\*PASS_LIVE\*\*** | anchor constant while \`current_full_end_abs\` varies 13/11/12 |

\| E09 | rejection cross boundary | **\*\*INSUFFICIENT_EVIDENCE\*\*** | not deterministically inducible from a fixed fixture/seed |

\| E10a | controlled multi-request (offline \`enqueue\`) | **\*\*INCOMPLETE\*\*** | target batch never formed — see §5 |

\| E10b | concurrent HTTP / barrier | **\*\*EXPECTED_UNSUPPORTED\*\*** | same gate, EngineCore abort |

\| E10c | \`n=2\` | **\*\*EXPECTED_UNSUPPORTED\*\*** | vLLM API: greedy ⇒ n=1 |

\| E11a | sequential row reuse, one engine | **\*\*PASS_LIVE\*\*** | see §6 |

\| E11b | persistent row index | **\*\*NOT_OBSERVED\*\*** | \`idx_mapping\` not instrumented |

\| E11c | strict \`[A,B]→[B,A]\` swap | **\*\*NOT_OBSERVED\*\*** | needs batch>1, unreachable |

\| E12a–d | graph / async / prefix / TP2 | **\*\*PASS_LIVE\*\*** | explicit \`reason=\` P2 rejections |

\| E12e | mixed prefill/decode | **\*\*EXPECTED_UNSUPPORTED\*\*** | aborts EngineCore |

\| E12f | dynamic K | **\*\*NOT_RUN\*\*** | no CLI surface |

\| W01 | write/Target isolation | **\*\*PASS_LIVE\*\*** | 84/84 identical, see §8 |

\| W02 | slot oracle | **\*\*INCOMPLETE\*\*** | not independently recomputed |

\| O01 | operator inputs (L4) | **\*\*PASS_LIVE\*\*** | see §7 |

\| O02 | kernel read behaviour (L5) | **\*\*NOT_OBSERVED\*\*** | not attempted |

\| L01 | device lifetime | **\*\*INSUFFICIENT_EVIDENCE\*\*** | see §9 |

\| F01 | Final non-debug confirmation | **\*\*PASS_LIVE\*\*** | see §10 |

\| G01 | general online mixed arrivals | **\*\*EXPECTED_UNSUPPORTED\*\*** | \`UNSUPPORTED_WITH_ENGINE_ABORT\` |



**## 4. Controlled multi-request — construction**



\`LLM.enqueue(prompts, sampling_params) -> list[str]\` and \`LLM.wait_for_completion()\` exist at

this revision (\`vllm/entrypoints/llm.py:483,529\`). The driver queues **\*\*both\*\*** prompts before

the engine steps, so they should be co-admitted. It does not touch the scheduler, does not

monkeypatch scheduling, and does not disable the mixed gate. Route parameters match the

verified HTTP launcher exactly; \`temperature=0\`, \`n=1\`, K=3, W=64, seed 1024.



Prompts A and B are the **\*\*same token length\*\*** (5 each, verified with the engine tokenizer).



**## 5. E10 — first blocker (the target batch is never formed)**



Four constructions attempted; **\*\*none produced \`num_reqs=2\` with all active rows decoding\*\***:



\| construction | result |

\|---|---|

\| two concurrent HTTP requests | EngineCore abort (mixed) |

\| two concurrent, barrier-synchronized, equal length | EngineCore abort (mixed) |

\| \`n=2\` (same-step batch by construction) | HTTP 400, greedy ⇒ n=1 |

\| **\*\*offline \`enqueue([A,B])\` then \`wait_for_completion()\`\*\*** | **\*\*EngineCore abort (mixed)\*\*** |

\| offline \`enqueue\` with \`max_num_batched_tokens=40960\` (the one sanctioned correction) | **\*\*EngineCore abort (mixed), identical\*\*** |



The scheduler dump is the ground truth, identical in both offline runs:



\`\`\`

Dumping scheduler output for model execution: SchedulerOutput(

  scheduled_new_reqs=[NewRequestData(req_id=1-b573de99, prompt_token_ids_len=5, …)],

  …

  num_scheduled_tokens={'1-b573de99': 5, '0-a124c49f': 4},  total=9)

\`\`\`



**\*\*Only the second request is newly scheduled\*\***, with 5 tokens — its prefill — while the first

request consumes 4 tokens of decode (K+1). So request A begins decoding before request B is

admitted, and the step contains both a prefilling and a decoding row → mixed → the route

fail-closes.



\`draft_slots\` is **\*\*not\*\*** the limiter (\`max_num_new_slots_for_drafting\` is 0 for non-parallel

EAGLE3), and raising the token budget changed nothing. Per instruction, no further retries and

no scheduler modification were attempted.



**\*\*Scope statement:\*\*** this is a blocker of the *\*tested construction\** on this build. It does not

prove pure-decode multi-request is impossible in principle; it does show that

**\*\*batch > 1 is unreachable through every interface available here\*\***, and that the failure mode

is a **\*\*service-wide EngineCore abort\*\***.



**## 6. E11 — sequential row reuse (PASS_LIVE)**



One engine, no restart, three batches \`A → C → A\`:



\`\`\`

0-b4c69d84  proposals=15 complete=15 not_truncated=15   epochs 0..14

1-949ac6a6  proposals=16 complete=16 not_truncated=16   epochs 15..30

2-8ce8559c  proposals=15 complete=15 not_truncated=15   epochs 31..45

oracle divergences 0 | active-row equality 138/138 | trace_error 0 | aborts 0

A_first  = ' Paris. The capital of Germany is '

A_repeat = ' Paris. The capital of Germany is '   <- byte-identical

\`\`\`



Epoch ranges are **\*\*strictly disjoint per request\*\***, each request's proposals are complete, and

the repeated prompt reproduces its output exactly — no stale state carried across requests in

the same engine.



**\*\*\`ROW REUSE\` is NOT given a row-index PASS\*\***: \`idx_mapping\` / persistent row index is not

instrumented, so reuse is *\*inferred\** from correct per-request isolation, not observed. Strict

\`[A,B]→[B,A]\` swap reorder is \`NOT_OBSERVED\` (needs batch>1). These are listed separately, not

bundled into one PASS.



**## 7. Operator inputs (PASS_LIVE, still Level 4)**



Draft/Target attribution is by block-table shape and is \*\*independent of whether the oracle

matched\*\*. Unmatched and Target calls are **\*\*counted, not filtered\*\***:



\| run | draft \`[1,2]\` | draft matching consumer | target | target matching |

\|---|---|---|---|---|

\| B_on | 33 | 33 | 367 | 0 |

\| CL_SEQ_on | 18 | 18 | 182 | 0 |

\| CL_WRITE_ISO | 18 | 18 | 182 | 0 |



\`actual_seq_lengths_kv == window_visible_exact\` held on **\*\*33/33\*\*** draft records (§25.5). The

comparison is against the Level-3 consumer boundary and the independent CPU oracle.



**\*\*Level boundary stated explicitly:\*\*** this is *\*operator-call argument\** evidence. It is **\*\*not\*\***

device-execution evidence and **\*\*not\*\*** kernel read-behaviour evidence. The \`LEVEL_4\` label does

not assert that all physical reads were observed.



**## 8. Write/Target isolation (W01 — PASS_LIVE)**



\`write_isolation\` snapshots \`BEFORE_WINDOW\` and \`AFTER_WINDOW\` around the window read

validation and Draft metadata assembly — the task's "before forward" point — on one identical

logical state. Per-step carriers legitimately change *\*between\** steps, so no cross-step

comparison is made.



\`\`\`

84 BEFORE/AFTER pairs:

  positions_active           identical 84/84

  slot_mappings_active       identical 84/84

  query_start_loc_cpu        identical 84/84

  canonical_full_tables      identical 84/84

  target_metadata_owner_id   identical 84/84

  target_metadata_layers     identical 84/84

  window_table changed       0        errors 0

\`\`\`



The window's read path does not mutate the write side or the Target.



**\*\*W02 (slot oracle) is INCOMPLETE.\*\*** \`expected_slot = physical_block\*B + offset\` was not

independently recomputed this round, and the FullSource values in the trace are truncated to

32 entries — insufficient for a general row oracle. Not claimed.



**## 9. Device lifetime (L01 — INSUFFICIENT_EVIDENCE)**



Established: the \`NO_SYNC\` run (0 device reads from the trace) produces behaviour identical to

the fully-instrumented run — same output, 92/92 proposals complete, 0 aborts. That shows the

result is **\*\*not observation-dependent\*\***.



Not established: that the previous reader's device read *\*happens-before\** the next overwrite.

No event/wait/stream instrumentation was added, and the task forbids adding a wait in the

debug tree to make a claim about Final. NO_SYNC output equality is a supplement, not a proof.



**\*\*No \`PRODUCTION_FIX_REQUIRED\` was raised\*\***: no missing dependency, no premature CPU-source

rewrite and no free/reuse error was observed. This is an absence of evidence, not evidence of

absence.



**## 10. Final non-debug confirmation (F01 — PASS_LIVE)**



Final overlay, \`DEBUG\` unset, small offline batch:



\`\`\`

llm build 28.36 s

  short          -> 16 tokens  ' Paris. The capital of Germany is Berlin'

  nonzero_anchor -> 16 tokens  ' The process of photosynthesis is essent'

no device error, engine remained usable, 0 processes left, NPU released

\`\`\`



No high-synchronisation trace. No profile was run: G-AR-STEP cannot close this round (see

§11), so the D2H/synchronisation profiling that closure would require was not triggered.



**## 11. Verdicts**



\`\`\`

SINGLE-REQUEST WINDOW                 : PASS

CONTROLLED MULTI-REQUEST PURE-DECODE  : INCOMPLETE

ROW REUSE / REORDER                   : reuse NOT_OBSERVED (row index not instrumented)

                                        sequential 3-request isolation PASS_LIVE

                                        strict swap reorder NOT_OBSERVED

WRITE/TARGET ISOLATION                : PASS

OPERATOR INPUTS                       : PASS  (Level 4; Level 5 NOT_OBSERVED)

DEVICE LIFETIME                       : OPEN

GENERAL ONLINE MIXED ARRIVALS         : UNSUPPORTED_WITH_ENGINE_ABORT

G-AR-STEP                             : OPEN

\`\`\`



\`G-AR-STEP: OPEN\` — not \`CLOSED FOR \<scope>\`, because the original frozen acceptance list

still has an unmet item: **\*\*controlled multi-request pure decode\*\***. A partial technical

conclusion is available (single-request semantics, write/Target isolation and operator inputs

all pass), but it must not be substituted for the total gate.



**## 12. Risk register**



1\. \*\*Service-wide abort on mixed arrivals — release blocker for any general online

   concurrency.\*\* A second request arriving while another decodes raises

   \`NotImplementedError\` inside the proposal path and kills the EngineCore; *\*both\** requests

   fail and the service stops serving. Even if this phase permits "mixed unsupported", the

   blast radius is not mitigated.

2\. **\*\*batch > 1 unreachable\*\*** on this route/build via HTTP, offline \`enqueue\`, or \`n=2\`.

3\. **\*\*Level 5 (kernel read behaviour) not observed\*\***; Level 4 is the evidence ceiling.

4\. **\*\*Device lifetime unproven\*\*** — no happens-before evidence for reader/overwrite ordering.

5\. **\*\*Slot oracle incomplete\*\*** (W02).

6\. \`dynamic_K\` negative gate untested (no CLI surface).



**## 13. P5 readiness**



\| question | answer |

\|---|---|

\| source/design preflight doable | **\*\*yes\*\*** — Final SHAs/trees, route and runtime are pinned and clean |

\| controlled route experiment has an eager baseline | **\*\*partially\*\*** — single-request eager is fully validated; controlled multi-request has no working baseline |

\| Graph ON | **\*\*still forbidden\*\*** — \`reason=Graph mode FULL_AND_PIECEWISE is not verified in P2\` |

\| release | **\*\*still HOLD\*\*** — see risk 1 |



Not entered. No production change. No performance claim.



**## 14. Artifacts**



\`\`\`

reports/P4b_R3_Closeout_Report_node133.md   this report

reports/P4b_R3_Final_Correctness_Report.md  §25/§26 retained unchanged

results/run_manifest.json                   17 runs, SHAs, native md5, route

results/case_results.json                   28-case ledger with statuses

results/CL_SEQ_on/                          E11 sequential (962 records)

results/CL_WRITE_ISO/                       BEFORE/AFTER isolation (670 records, 84 pairs)

results/CL_AB_on/, CL_AB_mbt/               E10 blockers + scheduler dump

results/CL_FINAL_NODEBUG/                   Final non-debug confirmation

results/E10_probe/                          n=2 API rejection

results/E10_E11_multireq/                   mixed-abort reproductions

results/E12_negative/, E12_graph/           gate rejections with explicit reasons

results/B_on/, B2_boundary/, B3_nosync/, B4_active_slice/, A1_off/, A2_off/, A3_off_F08/

debug/offline_batch_driver.py               controlled offline batch driver

debug/run_offline_batch.sh, run_multireq.sh, run_campaign.sh, run_negative_gates.sh

debug/test_p4b_r3a_plus_trace.py (36), test_p4b_r3_trace.py (8)   44 tests, all passing

\`\`\`



Stopped. No First Divergence in production business logic was found, so no

\`P4b_R3_First_Divergence_Report.md\` was raised; the E10 blocker is a route/scheduler

interaction, recorded above with its exact mechanism.
