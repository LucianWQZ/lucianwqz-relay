# P7-X Graph Base A3 Fix — GitHub Publication Audit

## 1. Audit Status

- Publication time: `2026-10-19 03:46:28 +0800 (CST)`
- GitHub user: `LucianWQZ`
- Repository: `https://github.com/LucianWQZ/vllm-ascend`
- Repository permission observed through GitHub CLI: `ADMIN`
- Target branch: `fix/p7x-graph-base-a3-g1g5`
- Publication action: normal non-force push of one new branch
- Pull request created: **No**
- Tag created: **No**
- Production source modified during publication: **No**
- Final publication verdict: **PASS**

## 2. Exact Source Identity

### vLLM-Ascend

| Field | Required | Verified local | Verified remote | Clean-room clone |
|---|---|---|---|---|
| Branch | `fix/p7x-graph-base-a3-g1g5` | exact | exact | exact |
| Commit | `13373fff637e819f3db125e05064f94cba3475a3` | exact | exact | exact |
| Tree | `739cde3de61e65be7cdbd187baebb6d17da04aee` | exact | exact via GitHub Git API | exact |
| Parent | `8cb4bed670f395c257c1233db944395159916009` | exact | exact via GitHub Git API | exact |
| Worktree | clean | clean | n/a | clean |

Published branch:

`https://github.com/LucianWQZ/vllm-ascend/tree/fix/p7x-graph-base-a3-g1g5`

### Pinned vLLM

| Field | Required | Verified |
|---|---|---|
| Commit | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | exact |
| Tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | exact |
| Worktree | clean and zero diff | yes |

The pinned vLLM repository was not modified.

## 3. Pre-publication Checks

The following checks completed before the push:

- GitHub CLI authentication was renewed through the official device flow.
- `gh auth status` identified the active account as `LucianWQZ`.
- `gh api user` returned `LucianWQZ`.
- `gh repo view LucianWQZ/vllm-ascend` returned the exact repository with `ADMIN` viewer permission.
- The local branch, commit, tree, parent and clean worktree matched the required values.
- The target GitHub branch did not exist (`GET git/ref/...` returned HTTP 404).
- The target commit was not already present in the GitHub repository before publication.
- The six A3 repair reports under `/Users/wenqingzhang/Desktop/Note/MRV2/` identify the same target commit/tree/parent.

## 4. Published Change Scope

Range:

```text
8cb4bed670f395c257c1233db944395159916009
..
13373fff637e819f3db125e05064f94cba3475a3
```

Summary:

```text
14 files changed, 1737 insertions(+), 52 deletions(-)
```

Files:

```text
M tests/ut/spec_decode/test_draft_window_graph_carrier.py
M tests/ut/spec_decode/test_draft_window_graph_characterization.py
A tests/ut/spec_decode/test_draft_window_graph_oracle.py
A tools/p7x_graph_g1_g5.py
M vllm_ascend/attention/attention_v1.py
M vllm_ascend/compilation/acl_graph.py
M vllm_ascend/envs.py
M vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py
M vllm_ascend/worker/v2/spec_decode/dflash/capture.py
M vllm_ascend/worker/v2/spec_decode/draft_window.py
M vllm_ascend/worker/v2/spec_decode/draft_window_eager.py
M vllm_ascend/worker/v2/spec_decode/draft_window_graph.py
M vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py
A vllm_ascend/worker/v2/spec_decode/draft_window_graph_oracle.py
```

This scope is limited to the Graph Base A3 isolation repair, tests, characterization-only observability, G1–G5 tooling, and the independent oracle. `git diff --check` passed.

## 5. Security and Publication Boundary Audit

The commit and changed-file set were inspected for publication hazards. No committed material was found matching:

- API keys, GitHub tokens, passwords, private keys or root credentials;
- model weights or large model artifacts;
- `/mnt/share/...` model paths;
- server logs, raw profiler output or internal benchmark artifacts;
- local `/Users/wenqingzhang/...` paths;
- Phase 1/Phase 2 performance result artifacts.

Only the already audited source/test/tool commit lineage was published. The external MRV2 Notes and device reports were not added to the repository.

## 6. Graph Safety State

Public Graph support remains frozen. Publication does not open any user-visible Graph route.

The pre-publication gate regression covered:

- characterization default-off behavior;
- zero provider/state when the characterization flag is off;
- continued rejection of `FULL`, `FULL_DECODE_ONLY`, and `PIECEWISE` public Graph Window routes.

Result: `5 passed`.

The new code remains a characterization candidate for the next A3 G1–G5 campaign, not a declaration of public Graph support.

## 7. Push Record

Command:

```bash
git push --set-upstream origin \
  fix/p7x-graph-base-a3-g1g5:fix/p7x-graph-base-a3-g1g5
```

Properties:

- ordinary push;
- no `--force` or `--force-with-lease`;
- no amend, rebase, squash or history rewrite;
- no other branch or tag was pushed;
- no pull request was created.

Remote head after push:

```text
13373fff637e819f3db125e05064f94cba3475a3
refs/heads/fix/p7x-graph-base-a3-g1g5
```

Remote Git object verification:

```json
{
  "sha": "13373fff637e819f3db125e05064f94cba3475a3",
  "tree": "739cde3de61e65be7cdbd187baebb6d17da04aee",
  "parents": ["8cb4bed670f395c257c1233db944395159916009"]
}
```

## 8. Protected Comparison Branches

The following remote refs were read before and after publication and did not change:

| Branch | Before | After |
|---|---|---|
| `spike/p7x-draft-window-graph-patch` | `8cb4bed670f395c257c1233db944395159916009` | `8cb4bed670f395c257c1233db944395159916009` |
| `perf/p7x-draft-window-hotpath` | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |

## 9. Clean-room Recovery Verification

An independent clone was created without reusing the source repository `.git` directory or worktree:

```text
/private/tmp/p7x-graph-a3-publication.1uNCaq/vllm-ascend
```

Clone command:

```bash
git clone \
  --branch fix/p7x-graph-base-a3-g1g5 \
  --single-branch \
  https://github.com/LucianWQZ/vllm-ascend.git \
  /private/tmp/p7x-graph-a3-publication.1uNCaq/vllm-ascend
```

Observed:

```text
HEAD   = 13373fff637e819f3db125e05064f94cba3475a3
tree   = 739cde3de61e65be7cdbd187baebb6d17da04aee
parent = 8cb4bed670f395c257c1233db944395159916009
status = clean
origin = https://github.com/LucianWQZ/vllm-ascend.git
```

Clean-room recovery therefore reproduces the exact published Git objects.

## 10. Final Repository State

- Local vLLM-Ascend: exact target branch/SHA/tree, clean, tracking the new origin branch.
- Local vLLM: exact pinned SHA/tree, clean, zero diff.
- Remote target branch: exact target SHA.
- Remote commit tree and parent: exact.
- Original Graph spike and performance branches: unchanged.
- Outstanding publication items: none.
- Remaining engineering step: Node101 A3 G1–G5 revalidation using this exact commit.

## 11. Final Verdict

```text
GITHUB_PUBLICATION: PASS
COMMIT: 13373fff637e819f3db125e05064f94cba3475a3
TREE: 739cde3de61e65be7cdbd187baebb6d17da04aee
PUBLIC GRAPH SUPPORT: STILL FROZEN
NEXT: NODE101 A3 G1-G5 REVALIDATION
```
