# P7-X Clean-room Restore Report

## Scope

Verified on 2026-10-15 (Asia/Shanghai) from exact parent
`4753742ab181920292c504a79eedecf9b428ae1b` to final commit
`c1c2129aa49ee1de381130729de73124a6ec893a` / tree
`384af8a0466f6aea2e73d6217f9802415b5ccd40`.

Each restore used a fresh local clone with `--no-hardlinks`; no current worktree,
build cache, stash, or untracked production file supplied the restored content.

## Full diff

- Temporary clone: `/tmp/p7x-full-a9Ay5V/repo`
- Checked out exact parent.
- `git apply --check P7X_Final_Full_Diff.patch`: PASS.
- Applied patch, staged all content, and ran `git write-tree`.
- Restored tree: `384af8a0466f6aea2e73d6217f9802415b5ccd40`.
- Verdict: exact tree match.

## Format-patch series

- Temporary clone: `/tmp/p7x-am-xEWhDq/repo`
- Checked out exact parent.
- Applied both binary-safe patches with `git am` in lexical order: PASS.
- Restored tree: `384af8a0466f6aea2e73d6217f9802415b5ccd40`.
- The local restored commit ID differs because `git am` creates new committer
  metadata; authorship/messages/order and final tree are preserved.
- Verdict: exact tree match.

## Git bundle

- `git bundle verify P7X_Final.bundle`: PASS.
- Bundle ref:
  `c1c2129aa49ee1de381130729de73124a6ec893a refs/heads/feature/p7x-nongraph-completion`.
- Required prerequisite: `4753742ab181920292c504a79eedecf9b428ae1b`.
- Temporary clone: `/tmp/p7x-bundle-UaEgeE/repo`.
- Fetched the branch from the bundle into a clone containing the prerequisite.
- Restored commit/tree:
  `c1c2129aa49ee1de381130729de73124a6ec893a` /
  `384af8a0466f6aea2e73d6217f9802415b5ccd40`.
- Verdict: exact commit and tree match.

## Source boundary

- vLLM stayed at `84030bbe3d74d99bad477a3d2e37a973ccd8865c`,
  tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`, clean.
- The vllm-ascend source worktree was clean after the review-fix commit.
- No Node101 login, NPU execution, Graph work, or GitHub push occurred.

## Verdict

```text
P7-X LOCAL FREEZE RESTORE: VERIFIED
NPU: NOT VERIFIED ON P7-X FINAL
```

