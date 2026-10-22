# 持续开发提交和恢复

最新开发C12：`d15a510c2afba62b8a0e37aa574550852079fd13`，tree `e98f21c40345f5785aecd237722c86dd3a266640`。C1–C12完整提交清单见 `../return/COMMIT_LIST.txt`。均为本地提交，REMOTE_PUBLICATION=NOT_PERFORMED；没有push、PR、merge。

`../return/MRV2_C12_local_commits.bundle` 是以精确Repair7 `7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14` 为 prerequisite 的增量Git bundle。已在新的/tmp仓库仅fetch Repair7基线后verify/fetch，确认精确C12 SHA/tree，见 `../state/BUNDLE_VERIFY_C12.json`。恢复示例：

```sh
git -C /path/to/exact-repair7 bundle verify /path/to/MRV2_C12_local_commits.bundle
git -C /path/to/exact-repair7 fetch /path/to/MRV2_C12_local_commits.bundle HEAD:refs/heads/review/mrv2-c12
git -C /path/to/exact-repair7 rev-parse review/mrv2-c12 review/mrv2-c12^{tree}
```

bundle仅含跟踪源码，不含凭据、模型或忽略的二进制。运行环境须按 `执行环境恢复说明.md`、`state/C8_WORKER_LIVE_PROVENANCE.json`、run根`C6_RUNTIME_OVERLAY_MANIFEST.json` 重建并核验原有二进制来源，不能把旧venv editable源码当固定候选。不要覆盖现有工作树；先检查HEAD/status/进程。

固定C8设备候选和C10检查器候选保留。完整C8数值通过C10只读复核；C10本身没有新NPU模型运行。旧C2提交说明是早期检查点，不代表当前验收范围。
