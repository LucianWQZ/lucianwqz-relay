# P8-E GitHub Publication and Node101 Deployment Audit

## Final status

Publication and post-publish validation timestamp: `2026-10-14 16:58:55 CST` (`Asia/Shanghai`).

```text
GITHUB PUBLICATION: PASS
REMOTE FINAL SHA: 4753742ab181920292c504a79eedecf9b428ae1b
CLEAN-ROOM RECOVERY: PASS
NODE101 DEPLOYMENT SOURCE: READY
```

No production source, test, commit, or existing branch history was changed by this operation. The only remote mutation was creation of `refs/heads/feature/p7-eager-completion` at the already-frozen Final commit. No company server was accessed.

## Historical blocked audit

The earlier audit was correctly recorded as blocked because the Final commit was not yet present on GitHub and the local GitHub credential was invalid. On `2026-10-14`, the user explicitly authorized GitHub CLI reauthentication and branch publication. The credential was restored, the remote was re-audited, and the exact branch was then published without force, rebase, squash, amend, or merge into `lucian-dev`.

## Exact publication identity

### vLLM

- Local repository: `/Users/wenqingzhang/Desktop/vllm/vllm`
- GitHub repository: `https://github.com/LucianWQZ/vllm.git`
- Local branch: `lucian-dev`
- Commit: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- Tree: `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`
- Local status after publication: clean
- Remote availability: the commit is contained by `origin/lucian-dev` and `origin/main`
- Prototype guard: no `DraftAttentionReadInputs` symbol was found in the clean-room checkout

### vLLM-Ascend

- Local repository: `/Users/wenqingzhang/Desktop/vllm/vllm-ascend`
- GitHub repository: `https://github.com/LucianWQZ/vllm-ascend.git`
- Branch: `feature/p7-eager-completion`
- Commit: `4753742ab181920292c504a79eedecf9b428ae1b`
- Tree: `b7e525c3c9d45617ad1023ad45c6948c466a3631`
- Upstream tracking: `origin/feature/p7-eager-completion`
- Local status after publication: clean
- P8 production commit: none

## Publication safety gate

The delivery range was audited directly from Git:

```text
base = 841dc6ccdb134eab7ad09008859834d0572ee83f
head = 4753742ab181920292c504a79eedecf9b428ae1b
28 files changed, 15405 insertions(+), 10 deletions(-)
```

Results:

- Both source repositories had empty `git status --porcelain --untracked-files=all` output.
- The vLLM-Ascend stash list was empty.
- Origin URLs exactly matched the user-approved `LucianWQZ` repositories.
- The exact 16-commit linear delivery history was present; no commit was rewritten.
- Changed-path checks found no model weights, logs, profiler output, benchmark dumps, P8 freeze content, or server evidence in the production range.
- Content checks found no `/mnt/share/` path, private-key marker, AWS access key, GitHub token, obvious API-key/password assignment, or root credential.
- No unusually large added text file was found.
- Notes, freeze artifacts, models, server logs, and raw benchmark/profiler data remained outside the production repository.

## Remote audit and push

Before the push:

```bash
git fetch origin --prune
git ls-remote --heads origin refs/heads/feature/p7-eager-completion
```

The branch did not exist, so there was no conflicting remote SHA. The exact ordinary push was:

```bash
git push -u origin feature/p7-eager-completion
```

No `--force` or `--force-with-lease` option was used. Immediate remote verification returned:

```text
4753742ab181920292c504a79eedecf9b428ae1b refs/heads/feature/p7-eager-completion
```

`git branch -vv` then showed the local branch tracking `origin/feature/p7-eager-completion` at the same commit.

## GitHub-only clean-room recovery

Clean-room root:

```text
/private/tmp/mrv2-p8-github-cleanroom.XGWH5i
```

No current `.git`, worktree, build cache, local bundle, local patch, or P8 freeze artifact was used as a source. The repositories were cloned from GitHub:

```bash
git clone --branch feature/p7-eager-completion --single-branch \
  https://github.com/LucianWQZ/vllm-ascend.git \
  /private/tmp/mrv2-p8-github-cleanroom.XGWH5i/vllm-ascend

git clone --branch lucian-dev --single-branch \
  https://github.com/LucianWQZ/vllm.git \
  /private/tmp/mrv2-p8-github-cleanroom.XGWH5i/vllm

git -C /private/tmp/mrv2-p8-github-cleanroom.XGWH5i/vllm \
  checkout --detach 84030bbe3d74d99bad477a3d2e37a973ccd8865c
```

Verification:

| Repository | HEAD | Tree | Status |
|---|---|---|---|
| clean-room vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | clean |
| clean-room vLLM-Ascend | `4753742ab181920292c504a79eedecf9b428ae1b` | `b7e525c3c9d45617ad1023ad45c6948c466a3631` | clean |
| original vLLM | same | same | clean |
| original vLLM-Ascend | same | same | clean |

The tree hashes prove that the GitHub clone reproduces the frozen local source exactly.

## Clean-room static smoke

The following was run against the clean-room source with `PYTHONPATH` pointing only at the two clean clones and `VLLM_VERSION=0.29.0`:

1. `compileall` for `worker/v2/spec_decode`, `worker/v2/attn_utils.py`, and `attention/attention_v1.py`: **PASS**.
2. Imports of:
   - `draft_window`
   - `draft_window_eager`
   - `draft_window_eager_capability`
   - `draft_window_async`
3. Every imported module's `__file__` was checked and pointed into the clean-room vLLM-Ascend clone: **PASS**.
4. Core P7 capability and async tests:

   ```text
   tests/ut/spec_decode/test_draft_window_eager_capability.py
   tests/ut/spec_decode/test_draft_window_async.py
   45 passed, 1 warning in 0.19s
   ```

On a raw source checkout, the first unbootstrapped import correctly exposed two installation/runtime prerequisites: generated `vllm_ascend._build_info` and `torch_npu`. The successful host smoke therefore used the repository's own `tests/ut/conftest.py` CPU/NPU mock bootstrap. This is not a source-transport difference; Node101 must install/build the package in its NPU environment before runtime validation.

## Which GitHub branch contains the complete Mac Final

The complete production lineage from the original vLLM-Ascend feature base to the frozen Mac Final is published on exactly this branch:

```text
feature/p7-eager-completion
```

Useful GitHub views:

- Branch: `https://github.com/LucianWQZ/vllm-ascend/tree/feature/p7-eager-completion`
- Commit history: `https://github.com/LucianWQZ/vllm-ascend/commits/feature/p7-eager-completion`
- Base-to-Final comparison: `https://github.com/LucianWQZ/vllm-ascend/compare/841dc6ccdb134eab7ad09008859834d0572ee83f...feature/p7-eager-completion`

Equivalent local inspection after fetch:

```bash
git log --graph --oneline \
  841dc6ccdb134eab7ad09008859834d0572ee83f..origin/feature/p7-eager-completion

git diff --stat \
  841dc6ccdb134eab7ad09008859834d0572ee83f..origin/feature/p7-eager-completion

git diff \
  841dc6ccdb134eab7ad09008859834d0572ee83f..origin/feature/p7-eager-completion
```

## Node101 source recovery commands

```bash
git clone https://github.com/LucianWQZ/vllm.git
git -C vllm checkout --detach 84030bbe3d74d99bad477a3d2e37a973ccd8865c

git clone --branch feature/p7-eager-completion --single-branch \
  https://github.com/LucianWQZ/vllm-ascend.git

git -C vllm-ascend rev-parse HEAD
git -C vllm-ascend rev-parse 'HEAD^{tree}'
git -C vllm-ascend status --porcelain --untracked-files=all
```

Expected vLLM-Ascend values:

```text
HEAD = 4753742ab181920292c504a79eedecf9b428ae1b
tree = b7e525c3c9d45617ad1023ad45c6948c466a3631
status = empty
```

## Conditional return-to-P7 rule

If Node101 produces `RETURN_TO_P7_Mandatory_Gap_Report.md`, production must not be patched directly on the server. Create a new local feature branch from `4753742ab181920292c504a79eedecf9b428ae1b`, implement only owner-confirmed mandatory gaps, repeat Codex implementation, independent review, adjudication/fix, and freeze, publish the new Final, and require Node101 to clean-fetch it. NPU evidence from the old SHA does not automatically transfer to a new SHA.

Possible gaps such as TP16, prefix cache, async, FlashComm, SP, or DSA-CP remain out of scope until the owner explicitly marks them mandatory.

## Evidence boundary

This PASS proves only:

- GitHub transport of the exact production history;
- exact source/tree recovery;
- clean source identity;
- host compile/import behavior under the repository's CPU test bootstrap;
- core P7 static capability/async contracts.

It does **not** prove:

- NPU runtime correctness;
- actual Draft Attention physical read-set;
- device stream/completion lifetime;
- performance;
- Graph support;
- resolution of `G-MIXED`.

Current product state remains:

```text
Graph track: FROZEN
Graph user gate: FAIL-CLOSED
Eager NPU: NOT VERIFIED
Eager performance: NOT VERIFIED
G-MIXED: OWNER_BLOCKED / RELEASE BLOCKER
Eager release: HOLD
Full feature release: HOLD
```
