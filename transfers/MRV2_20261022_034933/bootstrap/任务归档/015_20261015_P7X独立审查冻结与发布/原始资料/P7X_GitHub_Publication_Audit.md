# MRV2 Draft Sliding Window — P7-X GitHub Publication Audit

## 1. Publication Result

- Publication timestamp: `2026-10-15 10:48:11 CST`
- Repository: `https://github.com/LucianWQZ/vllm-ascend.git`
- Published branch: `feature/p7x-nongraph-completion`
- Push mode: ordinary non-force push with upstream tracking
- Remote divergence: none
- Pull request: not created

## 2. Exact Source Identity

### vLLM (read-only baseline)

- Repository: `https://github.com/LucianWQZ/vllm.git`
- HEAD: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- Tree: `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`
- Working tree: clean
- Production/test modifications in this publication: none

### vLLM-Ascend P7-X Final

- Local branch: `feature/p7x-nongraph-completion`
- Parent P8-E/P7-E Final: `4753742ab181920292c504a79eedecf9b428ae1b`
- P7-X original: `7e88db6ed31e7965f526ea6f49cc17101f4a65b4`
- P7-X review-fix / Final: `c1c2129aa49ee1de381130729de73124a6ec893a`
- Final tree: `384af8a0466f6aea2e73d6217f9802415b5ccd40`
- Local working tree: clean
- Tracking branch: `origin/feature/p7x-nongraph-completion`
- Tracking SHA: `c1c2129aa49ee1de381130729de73124a6ec893a`
- Local-to-tracking diff: empty

The two P7-X commits form an unmodified linear lineage above `4753742ab...`; no amend, squash, rebase, or force push was used. Both P7-X commits retain their `Signed-off-by` trailers.

## 3. Publication Safety Audit

The published range was audited before push. It contains only reviewed vllm-ascend source and tests. The changed-file boundary is:

- `tests/ut/spec_decode/test_draft_window.py`
- `tests/ut/spec_decode/test_draft_window_async.py`
- `tests/ut/spec_decode/test_draft_window_eager.py`
- `tests/ut/spec_decode/test_draft_window_eagle3.py`
- `tests/ut/spec_decode/test_draft_window_nongraph.py`
- `tests/ut/worker/test_attn_utils_v2.py`
- `vllm_ascend/worker/v2/attn_utils.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_async.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eager_capability.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eagle3.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py`

Audit results:

- API keys/passwords/private credentials: not found
- Model artifacts or model paths: not added
- Server logs, raw profiler artifacts, internal benchmark data: not added
- `/mnt/share/...` or internal machine/IP references: not added
- `/Users/wenqingzhang/Desktop/Note/MRV2` documents: not added
- Graph capture implementation/provider installation: not added by publication
- MRV1 changes: none
- vLLM changes/private prototype dependency: none

## 4. Push and Remote Verification

Executed push:

```bash
git push -u origin feature/p7x-nongraph-completion
```

No force option was used. Post-push verification established:

```text
refs/heads/feature/p7x-nongraph-completion
  SHA  = c1c2129aa49ee1de381130729de73124a6ec893a
  tree = 384af8a0466f6aea2e73d6217f9802415b5ccd40
```

Useful GitHub views:

- Branch: <https://github.com/LucianWQZ/vllm-ascend/tree/feature/p7x-nongraph-completion>
- Final commit: <https://github.com/LucianWQZ/vllm-ascend/commit/c1c2129aa49ee1de381130729de73124a6ec893a>
- P7-E Final to P7-X Final comparison: <https://github.com/LucianWQZ/vllm-ascend/compare/4753742ab181920292c504a79eedecf9b428ae1b...c1c2129aa49ee1de381130729de73124a6ec893a>

## 5. GitHub Clean-room Recovery

A disposable GitHub-only recovery was performed without reusing the local vllm-ascend `.git`, worktree, freeze bundle, or local patch.

- Disposable Git checkout: `/tmp/p7x-github-clean-0Vd6nR/repo`
- Remote branch: `feature/p7x-nongraph-completion`
- Recovered HEAD: `c1c2129aa49ee1de381130729de73124a6ec893a`
- Recovered tree: `384af8a0466f6aea2e73d6217f9802415b5ccd40`
- Recovered branch: `feature/p7x-nongraph-completion`
- Status: clean
- Tracked files: `4152`
- Lineage objects verified as commits:
  - `4753742ab181920292c504a79eedecf9b428ae1b`
  - `7e88db6ed31e7965f526ea6f49cc17101f4a65b4`
  - `c1c2129aa49ee1de381130729de73124a6ec893a`

The GitHub smart-HTTP checkout encountered poor throughput on the default edge. Recovery therefore used only official GitHub transports: Git metadata from the repository remote plus source hydration from GitHub codeload/API. No file from the local production worktree was copied into the recovered tree. Every P7-X changed file was compared by Git blob ID with the remote tree; omitted archive dot-files were fetched from GitHub and matched by blob ID. The resulting clean worktree resolves to the exact remote Final SHA/tree.

This establishes source publication and exact GitHub recovery. It is not a substitute for Node101 runtime reproduction.

## 6. Deployment Scope and Evidence Boundary

```text
P7-X local non-Graph static contract: PASS
P7-X NPU on Final SHA: NOT VERIFIED
Graph track: FROZEN
MRV1: UNCHANGED
vLLM: UNCHANGED
```

`LOCAL_STATIC_READY` does not mean `NPU_SUPPORTED`. Node101 must fetch this exact branch/SHA and rerun the second-round runtime campaign. NPU results from an earlier SHA do not automatically transfer to `c1c2129...`.

## 7. Node101 Source Handoff

```bash
git clone --branch feature/p7x-nongraph-completion --single-branch \
  https://github.com/LucianWQZ/vllm-ascend.git vllm-ascend
cd vllm-ascend
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git status --porcelain --untracked-files=all
```

Expected:

```text
HEAD = c1c2129aa49ee1de381130729de73124a6ec893a
tree = 384af8a0466f6aea2e73d6217f9802415b5ccd40
status = empty
```

The paired vLLM checkout must remain:

```text
HEAD = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status = empty
```

## 8. Credential and Network Note

No credential is recorded in this report. The `gh` CLI's pre-existing default token was invalid and the browser device flow could not complete through one GitHub edge. The successful ordinary Git push used the user's existing macOS Git credential and an official GitHub edge selected through transient per-command Git configuration. Repository remotes and system DNS were not rewritten.

## 9. Final Verdict

```text
P7-X GITHUB PUBLICATION: PASS
REMOTE DIVERGENCE: NO
CLEAN-ROOM RECOVERY: PASS
SECURITY AUDIT: PASS
NODE101 EXACT SOURCE/RUNTIME REPRODUCTION: READY TO START
```
