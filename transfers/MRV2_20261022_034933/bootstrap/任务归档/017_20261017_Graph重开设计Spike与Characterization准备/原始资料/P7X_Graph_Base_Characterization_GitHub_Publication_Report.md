# P7-X Graph Base Characterization Candidate — GitHub Publication Report

## 1. Report Status

| Field | Value |
|---|---|
| Publication time | 2026-10-17 14:49:05 CST |
| Purpose | Make the exact Graph characterization candidate fetchable by the company A3 server for G1–G5 experiments |
| GitHub repository | `https://github.com/LucianWQZ/vllm-ascend` |
| Published branch | `spike/p7x-draft-window-graph-patch` |
| Published commit | `8cb4bed670f395c257c1233db944395159916009` |
| Published tree | `899899c23fdc87acaed49c889eecd1f7889ad9c4` |
| Publication result | **PASS — exact remote SHA verified** |
| Force push | **NO** |
| Pull request | **NOT CREATED** |
| Public Graph support | **STILL FROZEN** |
| NPU status | **NOT RUN on this candidate** |

This is an experimental source branch for company-NPU characterization. It is not a product-support branch and must not be interpreted as closing Graph correctness, performance, topology, or release gates.

## 2. Repository Boundary

### vLLM-Ascend

```text
local path: /Users/wenqingzhang/Desktop/vllm/vllm-ascend
branch:     spike/p7x-draft-window-graph-patch
HEAD:       8cb4bed670f395c257c1233db944395159916009
tree:       899899c23fdc87acaed49c889eecd1f7889ad9c4
status:     clean
```

### Pinned vLLM

```text
local path: /Users/wenqingzhang/Desktop/vllm/vllm
HEAD:       84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree:       f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status:     clean
modified:   no
```

No vLLM patch or private upstream API is part of this publication.

## 3. Exact Published Lineage

Git ancestry was checked locally and again through the GitHub commit API:

```text
1b7215c37d1e3c9d1edac1fc20bcad26917ca251
  perf(spec-decode): reduce MRV2 draft window hot-path overhead
    ↓
c43989aabd9b40a561987d39f4ba4516934f2f5b
  spike(spec-decode): prototype draft window graph capture patch
    ↓
8cb4bed670f395c257c1233db944395159916009
  spike(spec-decode): prepare graph window characterization
```

GitHub API evidence:

- `8cb4bed...` parent is exactly `c43989a...`;
- `c43989a...` parent is exactly `1b7215c...`;
- both spike commits retain their `Signed-off-by` trailers;
- no rebase, squash, amend, or history rewrite was performed.

## 4. Authentication and Repository Ownership

GitHub CLI was re-authorized through the official browser/device flow. No Personal Access Token was requested from or printed by the user.

Verified state:

```text
authenticated account: LucianWQZ
nameWithOwner:          LucianWQZ/vllm-ascend
repository URL:         https://github.com/LucianWQZ/vllm-ascend
default branch:         main
Git protocol:           https
```

The existing remotes were preserved:

```text
origin   https://github.com/LucianWQZ/vllm-ascend.git
upstream https://github.com/vllm-project/vllm-ascend.git
```

Only `origin` and only the experimental branch were pushed. `main`, `upstream`, and all other branches were untouched.

## 5. Remote State Before and After Push

Before publication:

```text
refs/heads/spike/p7x-draft-window-graph-patch: absent
```

Therefore there was no remote divergence and no force operation was necessary.

Executed push:

```bash
git push -u origin spike/p7x-draft-window-graph-patch
```

After publication:

```text
refs/heads/spike/p7x-draft-window-graph-patch
= 8cb4bed670f395c257c1233db944395159916009
```

The local branch now tracks:

```text
origin/spike/p7x-draft-window-graph-patch
```

The branch is currently reported by GitHub as unprotected. Company-side validation must therefore pin and verify the exact SHA rather than trusting the movable branch name alone.

## 6. GitHub Verification Evidence

Three independent remote checks agreed:

1. `git ls-remote --heads origin refs/heads/spike/p7x-draft-window-graph-patch`
2. GitHub branch API
3. GitHub commit API

All returned:

```text
8cb4bed670f395c257c1233db944395159916009
```

Links for review:

- Branch: <https://github.com/LucianWQZ/vllm-ascend/tree/spike/p7x-draft-window-graph-patch>
- Candidate commit: <https://github.com/LucianWQZ/vllm-ascend/commit/8cb4bed670f395c257c1233db944395159916009>
- Capture POC commit: <https://github.com/LucianWQZ/vllm-ascend/commit/c43989aabd9b40a561987d39f4ba4516934f2f5b>
- Compare from performance base: <https://github.com/LucianWQZ/vllm-ascend/compare/1b7215c37d1e3c9d1edac1fc20bcad26917ca251...8cb4bed670f395c257c1233db944395159916009>

No PR was created. GitHub printed a PR suggestion after push, but it was deliberately not followed.

## 7. What Was Uploaded

The published branch contains the two Graph spike commits above. Relative to `1b7215c...`, the Graph-specific delta is:

```text
13 files changed, 2378 insertions, 50 deletions
```

Changed files:

```text
M tests/ut/spec_decode/test_draft_window_graph_carrier.py
A tests/ut/spec_decode/test_draft_window_graph_characterization.py
M vllm_ascend/envs.py
M vllm_ascend/patch/__init__.py
M vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py
M vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py
A vllm_ascend/worker/v2/spec_decode/dflash/capture.py
M vllm_ascend/worker/v2/spec_decode/dflash/speculator.py
M vllm_ascend/worker/v2/spec_decode/draft_window.py
M vllm_ascend/worker/v2/spec_decode/draft_window_eager.py
M vllm_ascend/worker/v2/spec_decode/draft_window_graph.py
A vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py
M vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
```

### Capture POC commit

`c43989a...` introduced the Ascend-owned patched capture helper, Draft-private InputBuffers transport, capture identity/provider plumbing, cleanup, and carrier tests.

### Characterization commit

`8cb4bed...` added:

- strict default-off internal environment flag `VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH`;
- controlled DFlash/eligible DSpark candidate bootstrap;
- real-generation runtime carrier binding;
- capture identity registration from actual capture descriptors;
- bounded instance-owned G1–G5 recorder/session;
- G1 capture address, G2 refresh, G3 read oracle, G4 write oracle, and G5 timeline observation;
- exception cleanup and overwrite protection regression tests;
- no public product-gate enablement.

## 8. What Was Not Uploaded

The publication did **not** include:

- any vLLM modification;
- models or `/mnt/share/...` data;
- company server logs or traces;
- NPU profiler artifacts;
- local Note documents or raw internal evidence;
- credentials, PAT text, or device-flow code in Git history;
- a PR, release, tag, merge, or default-branch change;
- feature-specific TP16/Async/Prefix/DSA/DSA-CP/Eagle3 Graph enablement.

The local Markdown reports under `/Users/wenqingzhang/Desktop/Note/MRV2/` are outside the source repository and were not pushed by this command.

## 9. Pre-publication Validation State

The exact candidate commit had the following local evidence before publication:

| Check | Result | Boundary |
|---|---|---|
| Candidate + P6 carrier | `65 passed` | CPU/static |
| P1–P7X/P5/P6/Graph targeted | `444 passed` | CPU/static |
| attn_utils / attention_v1 / BlockTables | `101 passed` + `23 subtests` | host/static |
| Full `tests/ut/spec_decode` | `654 passed, 13 skipped, 7 failed` | 7 failures stop at host backend selection; suite is not reported as full PASS |
| Ruff / format | PASS | changed files |
| targeted Mypy | PASS | 8 source files |
| compileall / diff-check | PASS | local |
| repository pre-commit | environment blocked | actionlint dependency fetch timed out; not a code PASS |

No NPU experiment was run as part of publication.

## 10. Exact Company A3 Checkout Procedure

Recommended clean checkout:

```bash
git clone https://github.com/LucianWQZ/vllm-ascend.git
cd vllm-ascend
git fetch origin spike/p7x-draft-window-graph-patch
git checkout --detach 8cb4bed670f395c257c1233db944395159916009

git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git status --porcelain
```

Expected:

```text
HEAD = 8cb4bed670f395c257c1233db944395159916009
tree = 899899c23fdc87acaed49c889eecd1f7889ad9c4
status = empty
```

Pinned vLLM must separately be checked out at:

```text
84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
```

The internal experiment is activated only for the reviewed base route with:

```bash
export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1
```

This variable is for characterization only. It must not be installed in a production service configuration.

The detailed experiment sequence is in:

`/Users/wenqingzhang/Desktop/Note/MRV2/P7X_Graph_NPU_Full_Campaign_v2.md`

## 11. Required G1–G5 Evidence

The company NPU campaign must still prove:

| Gate | Required device evidence |
|---|---|
| G1 | actual captured Draft operator/task address equals persistent Window carrier |
| G2 | same address refreshes A/B/A' content without stale/early overwrite |
| G3 | actual physical read-set equals the CPU Window oracle |
| G4 | full slot, positions, query, Target metadata/cache, and KV write remain unchanged |
| G5 | replay/consumer/update effective generation and true stream completion/lifetime |

If G1 fails, stop. If any of G2–G5 fails, preserve artifacts and return to local adjudication. CPU snapshots do not substitute for these device facts.

## 12. Remaining Unsupported Scope

The candidate validator intentionally excludes:

- TP/TP16 and other parallel topologies;
- async scheduling;
- prefix cache;
- chunked/mixed Graph combinations;
- multi-group;
- DSA, DSA-CP, SFA, MLA, indexer/QLI;
- Eagle3 Graph;
- DFlash2 Graph;
- unsupported hardware families.

These have implementation-ready designs but are not enabled by this branch.

## 13. Review Questions for Another AI

An independent reviewer should verify:

1. Does the branch and GitHub API expose exactly `8cb4bed...` with the stated parent chain?
2. Does the internal flag remain strict default-off?
3. Can CONFIG_OFF, FORCED_OFF, eager, unsupported method/backend/topology create any characterization state?
4. Is every provider/session/recorder instance-owned and bounded?
5. Does runtime binding reuse the real P3 generation without incrementing/re-materializing it?
6. Are slot/positions/query/Target/canonical source excluded from Window overrides?
7. Can a recorder or metadata-build exception leave a BOUND carrier active?
8. Does any code path remove or bypass the public Graph fail-closed gate?
9. Are G1–G5 outputs correctly described as observability rather than NPU proof?
10. Is the A3 handoff pinned to the SHA/tree rather than only the branch name?

## 14. Final Publication Verdict

```text
GITHUB PUBLICATION: PASS
REMOTE EXACT SHA MATCH: YES
FORCE PUSH: NO
PR: NOT CREATED
PINNED VLLM: CLEAN / UNCHANGED
PUBLIC GRAPH SUPPORT: STILL FROZEN
NPU GRAPH CORRECTNESS: NOT VERIFIED
NEXT: COMPANY A3 G1-G5 CHARACTERIZATION
```

