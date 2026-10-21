# P7X_A3_07_Raw_Text_Evidence — index

RUN_ID: `20261019_055109_13373fff`

LOGICAL_DOCUMENT: `P7X_A3_07_Raw_Text_Evidence.md`

This document is split into 6 independently readable Markdown parts.
Each part starts with its own RUN_ID, PART index and section list. No code block, traceback or log unit is cut mid-record.

## Parts

| Part | Sections | Bytes | SHA256 |
|---|---|---:|---|
| `P7X_A3_07_Raw_Text_Evidence.part001.md` | Filtering rule and counts, A0 result, A1 result (expected early gate), B fixed-contract result (full traceback), B partial v2 artifact, Host UT file outputs, test_draft_window_graph_characterization.log, test_draft_window_graph_carrier.log, test_draft_window_graph_binding.log, test_draft_window_graph_oracle.log | 22093 | `31a888a6fdfb11c6c3355976f8e42917d16fc96c4b9f1bf84385f34d71b6a6f2` |
| `P7X_A3_07_Raw_Text_Evidence.part002.md` | real_owner_regression.log, host_lifecycle.log, Helper / oracle / audit capability output, Oracle cases log, Repo audit on partial B artifact, Source snippets (exact SHA, file, function, line), capture.py — record capture then attach capture operand observer, draft_window_graph_characterization.py — attach rejects a pre-existing context, draft_window_graph_characterization.py — private isolation view + final metadata restore | 21126 | `6aed962799e8e4c569fda75e80417997364aa5de51a36a7cb5fd08caf17909b4` |
| `P7X_A3_07_Raw_Text_Evidence.part003.md` | draft_window_graph.py — bind_read_carrier isolation/read/write validation, draft_window_graph.py — read-carrier validation separated from write-carrier validation, attention_v1.py — update operator operand hook after graph_task_update_end, attention_v1.py — capture operator operand hook after graph_task_group_end, acl_graph.py — thread typed update binding to the real backend update, envs.py — experimental flag and artifact path, External scripts (full text) | 16286 | `8998173e05b44a2895477a43ca4eca703f1b7f09c7ae7177454481ba381b09b2` |
| `P7X_A3_07_Raw_Text_Evidence.part004.md` | driver_case.py (new) | 10952 | `b47d92c8c68f0baf2718e156364106107ed3e0b71adc18844a6673a5ba1f6e74` |
| `P7X_A3_07_Raw_Text_Evidence.part005.md` | independent_checker.py, env_graph_char.sh, sitecustomize.py, probe_import_provenance.py | 21093 | `225b5760dd8b2444a3a10ead14ab970beeadade62cf859c1aeb7ade9cf3ce250` |
| `P7X_A3_07_Raw_Text_Evidence.part006.md` | Old → new driver diff, Integrity checks for this document | 16762 | `b8b78699321ca6e3653e92421547982c88e1916732188f7ce5c3433b44b1d0d0` |

## Content mapping

- part001: filtering rules, A0/A1/B result JSON and the partial B artifact.
- part002: host UT/lifecycle logs used as PASS evidence.
- part003: helper/oracle/audit output and source snippets.
- part004+: external scripts and driver diff.

The full A0/A1/B raw result JSON is also in `P7X_A3_06_Evidence.part002.json`; the full command ledger is in parts 004/005 of 06.
