# P7-X Original Commit Manifest

## Repository identity

```text
repository: /Users/wenqingzhang/Desktop/vllm/vllm-ascend
branch: feature/p7x-nongraph-completion
base: 4753742ab181920292c504a79eedecf9b428ae1b
base tree: b7e525c3c9d45617ad1023ad45c6948c466a3631
head: 7e88db6ed31e7965f526ea6f49cc17101f4a65b4
head tree: 71800e2e250f0b4dc51aede643eebff55e39b404
```

## Original implementation commit

| SHA | Parent | Subject | Stat | Signed-off-by |
|---|---|---|---|---|
| `7e88db6ed31e7965f526ea6f49cc17101f4a65b4` | `4753742ab181920292c504a79eedecf9b428ae1b` | `feat(spec-decode): complete mandatory non-Graph draft windows` | 13 files, +1879/-100 | `Lucian <2207456347@qq.com>` |

This single commit is intentional: the capability gate, phase-aware consumer,
async lifetime and tests must land together. Splitting admission from its live
owner would create an intermediate commit that incorrectly allows an incomplete
route. It is independently reviewable and far below the prohibited monolithic
10k-line scale.

## Changed files

```text
M tests/ut/spec_decode/test_draft_window.py
M tests/ut/spec_decode/test_draft_window_async.py
M tests/ut/spec_decode/test_draft_window_eager.py
M tests/ut/spec_decode/test_draft_window_eagle3.py
A tests/ut/spec_decode/test_draft_window_nongraph.py
M tests/ut/worker/test_attn_utils_v2.py
M vllm_ascend/worker/v2/attn_utils.py
M vllm_ascend/worker/v2/spec_decode/draft_window.py
M vllm_ascend/worker/v2/spec_decode/draft_window_async.py
M vllm_ascend/worker/v2/spec_decode/draft_window_eager.py
M vllm_ascend/worker/v2/spec_decode/draft_window_eager_capability.py
M vllm_ascend/worker/v2/spec_decode/draft_window_eagle3.py
A vllm_ascend/worker/v2/spec_decode/draft_window_nongraph.py
```

No vLLM, MRV1, Graph-capture, scheduler, model weights, server evidence or
debug artifacts are part of this commit.
