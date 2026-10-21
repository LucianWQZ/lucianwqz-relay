# P7-X Performance GitHub Publication Audit

## Verdict

`P7-X PERFORMANCE GITHUB PUBLICATION: PASS`

Publication timestamp: `2026-10-16 00:41:54 CST` (`Asia/Shanghai`)

This audit covers publication of the single performance commit only. No code,
history, tag, pull request, or frozen feature branch was modified as part of
this publication operation.

## Repository and Branch

- Repository: `https://github.com/LucianWQZ/vllm-ascend.git`
- Published branch: `perf/p7x-draft-window-hotpath`
- Remote ref: `refs/heads/perf/p7x-draft-window-hotpath`
- Local repository: `/Users/wenqingzhang/Desktop/vllm/vllm-ascend`
- Push mode: normal non-force push
- Tracking relation: local branch tracks `origin/perf/p7x-draft-window-hotpath`

## Exact Local Identity Before Publication

| Item | Verified value |
|---|---|
| Branch | `perf/p7x-draft-window-hotpath` |
| Commit | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |
| Tree | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` |
| Parent | `c1c2129aa49ee1de381130729de73124a6ec893a` |
| Parent tree | `384af8a0466f6aea2e73d6217f9802415b5ccd40` |
| Subject | `perf(spec-decode): reduce MRV2 draft window hot-path overhead` |
| Signed-off-by | `Lucian <2207456347@qq.com>` |
| Distance from parent | exactly one commit |
| Working tree | clean, including untracked-file audit |

The frozen feature branch remained at
`c1c2129aa49ee1de381130729de73124a6ec893a` before publication.

The pinned vLLM repository was independently checked and remained clean at:

- commit: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- tree: `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`

## Exact Changed-file Boundary

The parent-to-performance diff contains exactly six Python files and no other
path:

1. `vllm_ascend/worker/v2/spec_decode/draft_window.py`
2. `vllm_ascend/worker/v2/spec_decode/draft_window_async.py`
3. `vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py`
4. `tests/ut/spec_decode/test_draft_window_runtime.py`
5. `tests/ut/spec_decode/test_draft_window_async.py`
6. `tests/ut/spec_decode/test_draft_window_nongraph.py`

Diff summary: `6 files changed, 103 insertions(+), 9 deletions(-)`.

The changed-path audit found no MRV1, ACL/CUDA graph, scheduler,
`model_runner_v1`, C/C++/kernel/build, deployment, or vLLM repository file.

## Security and Accidental-artifact Audit

The exact range
`c1c2129aa49ee1de381130729de73124a6ec893a..1b7215c37d1e3c9d1edac1fc20bcad26917ca251`
was inspected before push.

Results:

- no API key, GitHub token, cloud key, password assignment, private key, or
  credential pattern was found;
- no `/mnt/share`, `/home/t008`, Node101/server-log, aisbench, benchmark
  CSV/JSON, raw-profiler, private manifest, or `Note/MRV2` path was found;
- no model, large binary, generated artifact, server evidence, or internal
  deployment file was present;
- raw/numstat inspection showed six ordinary text-file modifications and no
  binary entry;
- `git diff --check` passed.

The two pattern-search commands used for security and prohibited-path scans
returned no matches. Their exit status `1` is the normal `rg` result for an
empty match set, not an audit failure.

## Existing Validation Evidence Confirmed

The existing optimization report was read rather than rerunning the
multi-hour campaign. It records:

| Scope | Recorded result | Classification |
|---|---|---|
| P7-X targeted plus `attn_utils_v2` | `364 passed` | CPU/host contract |
| Directly affected files | `73 passed` | CPU/host contract |
| BlockTables + `attention_v1` | `55 passed`, `23 subtests passed` | no NPU kernel proof |
| Full `tests/ut/spec_decode` | `621 passed, 13 skipped, 7 failed`, `2 subtests passed` | seven failures retained as failures |
| Exact-parent VWN comparison | same `7 failed, 2 passed` | failures pre-exist the performance commit |

The seven full-suite failures stop in pinned upstream `selector.py` with
`Invalid attention backend for None`, do not cross a changed file, and were
not reported as PASS.

Recorded static checks:

- Ruff: PASS
- Ruff format check: PASS
- targeted Mypy: PASS
- compileall: PASS
- `git diff --check`: PASS
- applicable local pre-commit hooks: PASS
- actionlint: NOT RUN because Go dependency download timed out; no workflow
  file changed
- gitleaks hook: NOT RUN because the host lacked `gitleaks` and `wget`; the
  six-file diff was independently pattern-audited

## Remote Conflict Check and Push

Before push, `git fetch origin --prune` and an exact `git ls-remote` check
proved:

- `origin/feature/p7x-nongraph-completion` was exactly
  `c1c2129aa49ee1de381130729de73124a6ec893a`;
- `refs/heads/perf/p7x-draft-window-hotpath` did not exist;
- therefore no remote branch would be overwritten.

The only publication command was:

```bash
git push -u origin perf/p7x-draft-window-hotpath
```

No `--force`, `--force-with-lease`, rebase, amend, squash, merge, PR creation,
or tag creation was performed.

## Remote Exact Verification

After push and fetch:

| Remote item | Verified value |
|---|---|
| Performance branch SHA | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |
| Performance branch tree | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` |
| Frozen feature branch SHA | `c1c2129aa49ee1de381130729de73124a6ec893a` |

`git ls-remote --heads origin` returned those exact two SHAs for their
respective refs. The frozen branch did not move.

## GitHub Clean-room Recovery

Disposable clone directory:
`/private/tmp/p7x-performance-github-cleanroom.t5awff/vllm-ascend`

The clone was created only from GitHub:

```bash
git clone --branch perf/p7x-draft-window-hotpath --single-branch \
  https://github.com/LucianWQZ/vllm-ascend.git \
  /private/tmp/p7x-performance-github-cleanroom.t5awff/vllm-ascend
```

Clean-room verification:

| Item | Verified value |
|---|---|
| HEAD | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |
| Tree | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` |
| Parent | `c1c2129aa49ee1de381130729de73124a6ec893a` |
| Parent object type | `commit` |
| Parent tree | `384af8a0466f6aea2e73d6217f9802415b5ccd40` |
| Working tree | clean, including untracked-file audit |
| Changed paths | the same exact six-file set |

No source file, local patch, bundle, cache, or production-worktree object was
copied into the clean-room clone.

## Post-publication Source State

- local vllm-ascend remained at the exact performance SHA/tree and clean;
- local vLLM remained at the pinned SHA/tree and clean;
- no source or test file was modified by the publication operation;
- Notes and audit artifacts were not committed or pushed.

## Known Limits

This publication proves exact source transport, branch isolation, GitHub
recoverability, commit/tree identity, and audited diff scope. It does not add
or claim NPU runtime, performance, Graph, or release evidence beyond the
pre-existing performance report. The actionlint and gitleaks hook environment
limitations remain explicitly recorded and are not converted into PASS.

`P7-X PERFORMANCE GITHUB PUBLICATION: PASS`
