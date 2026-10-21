**# P7X_A3_00_Return_Index**


RUN_ID: `20261019_055109_13373fff`

RUN_ROOT: `/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff`


**## 1. Overall conclusion**


```text

EXPERIMENT_EXECUTION_COMPLETE = false (device positive path blocked)

TEXT_EVIDENCE_HANDOFF_COMPLETE = true

BASE_G1_G5_VERIFIED = false

READY_FOR_LOCAL_FOLLOWUP = true

OVERALL_VERDICT = RETURN_TO_LOCAL_FIX

SECONDARY_VERDICT = DEVICE_EVIDENCE_BLOCKED

PUBLIC GRAPH SUPPORT = STILL FROZEN

SERVER PRODUCTION MODIFICATIONS = NONE

```


Source identity:


```text

vllm-ascend: 13373fff637e819f3db125e05064f94cba3475a3

tree       : 739cde3de61e65be7cdbd187baebb6d17da04aee

parent     : 8cb4bed670f395c257c1233db944395159916009

vLLM       : 84030bbe3d74d99bad477a3d2e37a973ccd8865c

tree       : f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee

```


The fixed-contract B attempt fails at startup capture with

`RuntimeError: capture operand observer is already attached`

(`dflash/capture.py:376` → `draft_window_graph_characterization.py:1006`).

The old canonical-sharing failure point is ****NOT_REACHED**** on device; the

host real-owner regression passes. No device G1–G5 PASS is claimed.


**## 2. File manifest**


SHA256 is over the original server file. The index itself is excluded from its own hash

to avoid self-reference. For split documents, each part has its own hash and the

logical document index lists the parts.


| File | Bytes | Records | SHA256 |

|---|---:|---|---|

| `P7X_A3_01_Report_CN.md` | 17828 | lines=451 | `b1acd397fa26d92f4ed1e07b676f190b55f41aee5a17f2a75306e1ef99ce59b9` |

| `P7X_A3_02_Execution_Record.md` | 48182 | lines=707 | `b12210008e4c41c1cbb2b1e6ee28b71add542403b745bcb0b9fc1202a2111aec` |

| `P7X_A3_03_Device_Facts.json` | 33952 | keys=23 | `5b247604b7df5c5321afa8ec06ab1fcdcc61458db7f4971efc3fca4b51ab1d42` |

| `P7X_A3_04_A0_A1_B_Record.md` | 9139 | lines=311 | `6b13df2a160eb6cb4e9dde584a2a962cb40a3d5bfbdce03c30a4db5d4aa67872` |

| `P7X_A3_05_G1_G5_Decisions.md` | 13624 | lines=320 | `93cda7d5deb2eb2e4d242dae68db34ca6aca754fa8e34f8531339908ab2fb6ea` |

| `P7X_A3_06_Evidence.json` | 5155 | 6 | `fd32430b290fc393120fbe8a5290ac0aedadfda2d01c3c555dffd62e89b7ef9b` |

| `P7X_A3_06_Evidence.part001.json` | 21553 | 5 | `2a918472ec80053690c23c40641d28fe2e7b665415327e78bce18e90b0204b62` |

| `P7X_A3_06_Evidence.part002.json` | 19225 | 4 | `5b61c39aeef6610fb0f5e567170e578ed22ab0e15b9dc135f4aa913a3a271deb` |

| `P7X_A3_06_Evidence.part003.json` | 26991 | 5 | `706c7de729f20ea7fd40252c2e939efcd20fc26b4f23ac8f4e7d3818f762f839` |

| `P7X_A3_06_Evidence.part004.json` | 31257 | 1 | `621ea4e579c43642fbe1ea92dfe76e90ebbe8db30061041ac9d921b14946fc9f` |

| `P7X_A3_06_Evidence.part005.json` | 42867 | 1 | `9f08e3e2f4020ee9e2cb0fb4f81b2577b162e6b6e0d1c5f2b0153c41dffe1125` |

| `P7X_A3_06_Evidence.part006.json` | 25538 | 3 | `35364e2256403887f5dfd46a2a0671287f83ed8d5c426db38536faeb956f1adf` |

| `P7X_A3_07_Raw_Text_Evidence.md` | 2912 | lines=28 | `b6b8fa975c2fe78fa72974e3b0dbb1a8c22ea8887e992d6a7040617376f16082` |

| `P7X_A3_07_Raw_Text_Evidence.part001.md` | 22093 | lines=433 | `31a888a6fdfb11c6c3355976f8e42917d16fc96c4b9f1bf84385f34d71b6a6f2` |

| `P7X_A3_07_Raw_Text_Evidence.part002.md` | 21126 | lines=393 | `6aed962799e8e4c569fda75e80417997364aa5de51a36a7cb5fd08caf17909b4` |

| `P7X_A3_07_Raw_Text_Evidence.part003.md` | 16286 | lines=306 | `8998173e05b44a2895477a43ca4eca703f1b7f09c7ae7177454481ba381b09b2` |

| `P7X_A3_07_Raw_Text_Evidence.part004.md` | 10952 | lines=259 | `b47d92c8c68f0baf2718e156364106107ed3e0b71adc18844a6673a5ba1f6e74` |

| `P7X_A3_07_Raw_Text_Evidence.part005.md` | 21093 | lines=500 | `225b5760dd8b2444a3a10ead14ab970beeadade62cf859c1aeb7ade9cf3ce250` |

| `P7X_A3_07_Raw_Text_Evidence.part006.md` | 16762 | lines=350 | `b8b78699321ca6e3653e92421547982c88e1916732188f7ce5c3433b44b1d0d0` |

| `P7X_A3_08_Failures_And_Limits.md` | 9464 | lines=229 | `5b704f54c289d6da88c1e34fcd0f5a7aa421cab20986cc3adecd12153286742c` |

| `RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md` | 8013 | lines=143 | `3abef7e1736ef38e30bb3a011f84826944d3f44fc7808fea1545c70ce5a5a873` |

| `SHA256SUMS` | 2799 | lines=28 | `bfb833a297224b59d0ffdf1334a24b5c9b75c7133d3e1e88f1b4174dc3dd9681` |

| `gate_status.json` | 8756 | 26 | `8fdf49d6863f4c990ac90f5a6ec6830e98c4009d8ab6aeb64acceb11c98c7102` |

| `independent_checker.log` | 923 | lines=32 | `9af05a1768c4dd2e3bfb5e884b833a74258eb4d091d7ca6cf6ef07464379c116` |

| `independent_checker.stderr.log` | 0 | lines=0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

| `independent_checker_final.log` | 923 | lines=32 | `b55574a5b6da222e66e4356622fdeed0709db981fefa950a3445e1a598aaea4f` |

| `independent_checker_final.stderr.log` | 0 | lines=0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

| `independent_checker_result.json` | 11988 | 26 | `c9ce79b11e0aa3c0ee7590e9fd38f95f5f73d25186cbc8ce2c5001411efb871d` |

| `P7X_A3_00_Return_Index.md` | this file | self | excluded (self-reference) |


**## 3. Case / attempt inventory**


| Case | Attempt | CMD | Device | Exit | Status |

|---|---|---|---|---|---|

| A0 | 1 | CMD-0017 | 5 | 0 | OK; 16 tokens match old contract; zero state |

| A1 | 1 | CMD-0018 | 5 | 2 expected | GRAPH_FROZEN early gate |

| B fixed `[7,14,28]` | 1 | CMD-0019 | 5 | 2 | capture observer re-attach |

| B_DIAG_CAP7 | 1 | CMD-0020 | 5 | 0 | eager-only diagnostic |

| B_DIAG_CAP14 | 1 | CMD-0021 | 5 | 0 | eager-only diagnostic |

| B_DIAG_CAP28 | 1 | CMD-0022 | 5 | 0 | eager-only diagnostic |

| B_DIAG_CAP28_INTROSPECT | 1 | CMD-0023 | 5 | 0 | inventory only |

| B_DIAG_CAP24_INTROSPECT | 1 | CMD-0024 | 5 | 2 | install rejects empty draft descriptors |

| HOST_UT | 1 | CMD-0011..0015 | none | 0 | 116 + 2 PASS |

| HOST_LIFECYCLE | 1 | CMD-0025 | none | 0 | 16 PASS |

| NEGATIVE | 1 | CMD-0026 | none | 0 | 31/31 MATCH |

| G3_ORACLE_HOST | 1 | CMD-0027 | none | 0 | 4 positive + 2 expected rejects |

| CROSS_AUDIT | 1/2 | CMD-0029/0037 | none | 0 | final 26 PASS / 0 OPEN / 0 FAIL |


**## 4. Missing evidence**


- Device capture completion for fixed `[7,14,28]` (blocked by GAP-001).

- Device BOUND / LIVE / REPLAY / CONSUMER / UPDATE events.

- Device `capture_operator` / `update_operator` operand records.

- Device G4 record and OFF/ON write/Target comparison.

- Device A/B/A′ for G2.

- G1 L3 ACL task internal binding.

- G3 physical read set (L5).

- G5 effective update generation and device completion/reuse (L6).

- Target logits/output numeric comparison.

- Device abort/exception lifecycle.

- msprof/NPU trace (not collected because B never reached replay).


**## 5. What the text can and cannot support**


| Claim | Supported? | Where |

|---|---|---|

| Exact source/runtime/fixture identity | YES | 01 §3, manifests, 06 part001 |

| A0 MRV2 baseline and deterministic output | YES | 04 §1, 06 part002 |

| A1 public gate fail-closed | YES | 04 §2, 06 part002 |

| B new capture observer defect | YES | 04 §3, 05, 08, 06 part002 |

| Host old-alias regression | YES (host only) | 06 part002, 07 part002 |

| Host G2 A/B/A′ / G4 record / G5 event recorder | YES (host only) | 05, 07 part002 |

| Host independent oracle and negatives | YES (host only) | 05 G3, 06 part003 |

| Device G1 operand equality | NO | OPEN |

| Device physical reads / KV writes | NO | OPEN/UNPROVEN |

| Device effective update generation / completion | NO | OPEN |

| Base G1–G5 PASS | NO | not claimed |

| Performance | NO | not run |


**## 6. Local requirement → file/section/JSON key**


| Local requirement | This handoff |

|---|---|

| Exact source SHA/tree/parent/clean | 01 §3; `manifests/source_identity.json` |

| Import provenance | 01 §3.3; `manifests/import_provenance.json`; 03 `import_provenance` |

| Fixture + weight hashes | 01 §3.5; `manifests/fixture.json`; `fixture_hashes.txt`; 03 `fixture` |

| MRV2 runtime identity | 01 §3/§6; 03 `mrv2`; 04 §1; `A0/result.json`; `B/artifact` |

| A0/A1/B control record | 04; 06 part002; 02 CMD entries |

| G1–G5 decisions | 05; 03 `g1`..`g5`; 06 part002/003 |

| Negative matrix | 05 negative; 03 `negative`; 06 part003 |

| Observability readiness | 03 `observability_readiness`, `case_registry` |

| Failures and limitations | 08 |

| Local gap/fix report | 09 |

| Full execution ledger | 02; 06 parts 004/005 |

| Raw text evidence | 07 index + parts 001..006 |

| Cross-artifact audit | `reports/independent_checker_result.json`; 06 part006 |

| Cleanup/integrity | 02 final; 03 `cleanup`; `raw/npu_after.txt`; `manifests/team_tools_verification.json` |

| Final verdict | 01 §12; 03 `decision`; `reports/gate_status.json` |


**## 7. Copy order**


1. `P7X_A3_00_Return_Index.md`

2. `P7X_A3_01_Report_CN.md`

3. `P7X_A3_02_Execution_Record.md`

4. `P7X_A3_03_Device_Facts.json`

5. `P7X_A3_04_A0_A1_B_Record.md`

6. `P7X_A3_05_G1_G5_Decisions.md`

7. `P7X_A3_06_Evidence.json` (index) + `part001..006`

8. `P7X_A3_07_Raw_Text_Evidence.md` (index) + `part001..006`

9. `P7X_A3_08_Failures_And_Limits.md`

10. `RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md`


Manifests (`manifests/*.json`), gate status, checker result and the command

ledger are referenced by evidence ID and may be copied after the ten records.


**## 8. Integrity checks**


- Independent checker final run: 26 checks, 26 PASS, 0 FAIL, 0 OPEN (`reports/independent_checker_final.log`).

- `CHK-025 deliverables/ten_files` PASS; all ten main deliverables are non-empty.

- Team tools: ORIGINAL_TEAM_TOOLS_UNCHANGED (2296 → 2296 files).

- vllm-ascend and vLLM working trees: clean.

- No campaign process remains.

- No credential is included.

- Split Markdown/JSON parts are independently parseable and are not cut mid-record.


**## 9. Final verdict block**


```text

P7-X GRAPH BASE A3 G1–G5 RERUN

\=============================


RUN_ID:

20261019_055109_13373fff

RUN_ROOT:

/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff

SOURCE:

13373fff637e819f3db125e05064f94cba3475a3


SOURCE / IMPORT / FIXTURE:

EXACT / PASS / EXACT


A0:

PASS

A1 EARLY GRAPH_FROZEN:

PASS

B OLD FIX POINT:

NOT_REACHED

B BIND / PUBLISH / REAL REPLAY:

NOT_RUN

ALIAS FIX VERDICT:

HOST_PASS_DEVICE_NOT_REACHED


G1 HOST OPERATOR:

OPEN

G1 ACL TASK INTERNAL:

OPEN


G2 HOST ABA:

PASS

G2 NPU ABA:

NOT_RUN

G2 CANONICAL SOURCE LINEAGE:

OPEN


G3 ORACLE:

PASS

G3 OPERATOR:

OPEN

G3 TASK:

OPEN

G3 PHYSICAL READ:

OPEN


G4 FULL WRITE / TARGET:

OPEN

G4 DEVICE KV WRITE:

OPEN

G4 TARGET NUMERIC:

NOT_RUN


G5 FIRST REPLAY SOURCE:

NOT_RUN

G5 UPDATE EFFECTIVE GENERATION:

OPEN

G5 COMPLETION / REUSE:

OPEN

G5 ABORT / EXCEPTION:

HOST_PASS_DEVICE_OPEN


NEGATIVE MATRIX:

PASS (host, 31/31)

CROSS-ARTIFACT AUDIT:

PASS (evidence consistency; not device L3/L5/L6)

COVERED / UNCOVERED DESCRIPTORS:

capture (4,28) partial; no runtime coverage

OBSERVATION EFFECTS:

host snapshots; not performance representative


OVERALL VERDICT:

RETURN_TO_LOCAL_FIX

ALL BLOCKERS:

capture operand observer re-attach (production defect)

READY FOR LOCAL FOLLOWUP:

YES

EXACT NEXT LOCAL TASK:

make capture observer attach idempotent across descriptors; add red test; rerun fixed [7,14,28]

READY FOR BATCH A:

NO


PUBLIC GRAPH SUPPORT:

STILL FROZEN


SERVER PRODUCTION MODIFICATIONS:

NONE


TEXT EVIDENCE HANDOFF:

COMPLETE


SOURCE UNCHANGED:

YES

OWN PROCESSES CLEANED UP:

YES

```
