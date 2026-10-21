# P7-X Final Commit Manifest

## Exact identity

```text
vLLM baseline: 84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM tree: f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
vllm-ascend P8/P7-E parent: 4753742ab181920292c504a79eedecf9b428ae1b
P7-X original: 7e88db6ed31e7965f526ea6f49cc17101f4a65b4
P7-X review-fix: c1c2129aa49ee1de381130729de73124a6ec893a
P7-X final tree: 384af8a0466f6aea2e73d6217f9802415b5ccd40
branch: feature/p7x-nongraph-completion
```

Both P7-X commits are signed off. The original was not amended, squashed, or
rebased. vLLM and MRV1 are unchanged.

## Lineage

```text
4753742ab  fix(spec-decode): address P7 eager capability review findings
  |
7e88db6ed  feat(spec-decode): complete mandatory non-Graph draft windows
  |
c1c2129aa  fix(spec-decode): address P7-X review findings
```

## Per-commit map

### `7e88db6ed31e7965f526ea6f49cc17101f4a65b4`

- Parent: `4753742ab181920292c504a79eedecf9b428ae1b`
- Scope: original P7-X non-Graph completion.
- Stat: 13 files, +1879/-100.
- Production: phase/current-extent contracts, TP topology, uncompressed DSA and
  DSA-CP provider classification, mixed/chunked/prefix carriers, bounded eager
  async owner, shared DSA-CP metadata builder correction.
- Tests: six P7-X source/consumer/lifecycle suites.
- Dependency: requires all P1-P8 history through parent; independently
  cherry-pickable only onto that exact parent lineage.

### `c1c2129aa49ee1de381130729de73124a6ec893a`

- Parent: `7e88db6ed31e7965f526ea6f49cc17101f4a65b4`
- Subject: `fix(spec-decode): address P7-X review findings`
- Stat: 9 files, +375/-29.
- Production:
  - pressure-only oldest-event backpressure and waitable NPU event adapter;
  - async capacity default/minimum tied to host `max_concurrent_batches`;
  - effective DSA-CP backend authority in topology context;
  - removal of an unused resident-snapshot pseudo-validation API.
- Tests:
  - async capacity 1/2, third inflight, reverse completion, abort-after-submit,
    query/wait failure, metadata retention, prefix and TP identity;
  - raw DSA-CP request versus effective false authority;
  - explicit Window-OFF DSA-CP shared-builder regression.
- Dependency: must follow the original P7-X commit.

## Changed production files across P7-X final

- `vllm_ascend/worker/v2/attn_utils.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_async.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eager_capability.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eagle3.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py`

No Graph capture file, upstream vLLM file, MRV1 file, model checkpoint, server
log, or profiler artifact is part of this lineage.

## Restore order

From exact parent `4753742...`, apply the two files in `format-patches/` using
`git am` in lexical order, or apply `P7X_Final_Full_Diff.patch` as an emergency
tree-only restore. The bundle is incremental and records the exact parent as a
prerequisite. Exact restored tree must be
`384af8a0466f6aea2e73d6217f9802415b5ccd40`.

