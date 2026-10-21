# Repair3 发布最终核验：VERIFIED

核验时间：2026-10-19T18:40:47.670268+00:00

普通 push 成功；GitHub API 与独立 gh 网络克隆均恢复 exact commit/tree/parent。Production 未修改，没有 PR/tag/force push，没有执行服务器实验。

## 网络原因与修复

scutil --proxy 显示系统 HTTP/HTTPS 代理 127.0.0.1:15236、SOCKS 127.0.0.1:15235；lsof 证实 Veee PID18817 正在监听。当前进程 HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY 均未设置，Git 无 http.proxy。gh credential helper 已正确安装。无残留 push 进程。

此前直连 TCP 超时；本次通过已配置 HTTP 代理 git ls-remote 成功（HEAD=5424573a93bc650e1f72261bae28ac0dfa13466c），随后 push 和 clone 均成功。证据支持 Git 未使用系统代理是直接原因；底层直连被何处丢弃未确定。无需 DNS/IPv6/SSH 绕行，没有改 hosts、防火墙、TLS 或全局代理。未读取代理订阅或秘密。

实际 push（Python subprocess timeout=180）：
```bash
git -c http.proxy=http://127.0.0.1:15236 push -u origin fix/p7x-graph-base-a3-repair3:fix/p7x-graph-base-a3-repair3
```
exit=0，new branch；仅本地新增正常 tracking 配置，单次代理覆盖在命令结束后失效。gh 身份 LucianWQZ，repo LucianWQZ/vllm-ascend，push/admin=true。

## 精确身份与独立克隆

commit=10cbf4c014fc6cc48a6fea611bb605cecdd54cfd
tree=28dddd6d1fc19e67270ee71b7b9e7fcd410ab3c9
parent=8198ab7a6df6a163316f5d4ed2126242bbeb4aa8
driver SHA256=7e6f2e5984430bc5231511960da2fdc9b073ddc58cfed8bfaed796498b70660d

API 与 clean clone 上述身份全部匹配，parent ancestry exit0，status为空。克隆路径仅是本机审计记录：/var/folders/jg/1291_6m930x__sj1qzy3kdsh0000gn/T/repair3-github-cleanroom-1tu7r9_4/vllm-ascend。

```bash
https_proxy=http://127.0.0.1:15236 gh repo clone LucianWQZ/vllm-ascend <fresh-temp>/vllm-ascend -- --single-branch --branch fix/p7x-graph-base-a3-repair3
```
exit0，真实网络下载，无本地对象共享/bundle/patch。gh 自动额外获取 upstream/main，origin仍为个人仓库；没有写远端 upstream。repair2、perf/p7x-draft-window-hotpath、feature/p7x-nongraph-completion 三条 ref 前后相同。

## 交付与状态

输入包重新生成，包内外 handoff 字节相同。为避免循环自哈希，handoff 的 ZIP hash 使用外部 Download Manifest 引用；包外 manifest 保存实际 ZIP bytes/SHA256。旧输入包 hash 已失效。所有 ZIP CRC、JSON、文件索引/hash通过。

PUBLICATION=VERIFIED
CLEAN_ROOM=VERIFIED
READY_FOR_A3_SMOKE=YES
READY_FOR_ALL_G1_G5_CLOSURE=NO
NEW_SHA_DEVICE_VERIFICATION=NOT_RUN
PUBLIC_GRAPH_GATE=STILL_FROZEN
FULL_PRECOMMIT=ENVIRONMENT_BLOCKED_actionlint_dependency_network

270 passed 为既有最终 Host 结果，本轮没有重新运行整套测试。设备 G1–G5、FULL_TARGET/KV、task/completion/physical read 仍待证。服务器使用新 exact SHA，不能继承旧 SHA 结果。

以下为此前失败时的原始报告，保留历史，不代表当前发布状态。

---
# P7-X Graph Base A3 Repair3 — Publication and Server Readiness Audit

核验时间：2026-10-19T18:25:21Z（2026-10-20 02:25:21 CST）  
目标仓库：`https://github.com/LucianWQZ/vllm-ascend`  
本报告记录真实发布尝试；历史“未发布”状态未被改写成成功。

## 1. 结论

| 项目 | 结论 |
|---|---|
| production 修改 | **NO** |
| GitHub CLI 身份 | `LucianWQZ`，有效，目标仓库权限 `ADMIN` |
| 普通 push | **FAILED**：`github.com:443` 连接阶段超时 |
| GitHub API 身份/权限 | **VERIFIED** |
| 目标远端分支 | **ABSENT** |
| 精确远端 commit/tree/parent | **NOT PUBLISHED** |
| clean-room clone | **NOT RUN — blocked by absent branch/publication** |
| PUBLICATION | **BLOCKED** |
| READY_FOR_A3_SMOKE | **NO** |
| READY_FOR_ALL_G1_G5_CLOSURE | **NO** |
| NEW_SHA_DEVICE_VERIFICATION | **NOT_RUN** |
| PUBLIC_GRAPH_GATE | **STILL_FROZEN** |

唯一发布阻塞不是认证、权限、源码或候选身份，而是本机到 `github.com` 的 Git smart-HTTPS 网络连接。`api.github.com` 可达，`github.com:443` 不可达。为了保留精确 Git SHA，本次没有用 GitHub API 生成的不同 commit 代替候选，也没有创建错误分支。

## 2. 范围与禁止项

本轮只核验并尝试发布已冻结 Repair3 候选；未修改 production/test，未 amend、rebase、force push、merge、tag 或创建 PR，未修改任何其他远端 ref，未执行服务器实验，未开放 Graph public Gate。

## 3. 本地候选身份

| 字段 | 实际值 | 预期 | 结果 |
|---|---|---|---|
| branch | `fix/p7x-graph-base-a3-repair3` | 同左 | PASS |
| commit | `10cbf4c014fc6cc48a6fea611bb605cecdd54cfd` | 同左 | PASS |
| tree | `28dddd6d1fc19e67270ee71b7b9e7fcd410ab3c9` | 同左 | PASS |
| parent | `8198ab7a6df6a163316f5d4ed2126242bbeb4aa8` | 同左 | PASS |
| worktree | clean | clean | PASS |
| driver SHA256 | `7e6f2e5984430bc5231511960da2fdc9b073ddc58cfed8bfaed796498b70660d` | 同左 | PASS |
| fixture manifest SHA256 | `1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4` | 同左 | PASS |

Commit subject：`fix(spec-decode): make graph observation passive and preserve capture layer identity`，包含 Signed-off-by。改动范围严格为六个文件：

- `tests/ut/spec_decode/test_draft_window_capture_observer.py`
- `tests/ut/spec_decode/test_draft_window_graph_characterization.py`
- `tests/ut/spec_decode/test_graph_repair2_campaign.py`
- `tools/p7x_graph_repair2.py`
- `vllm_ascend/attention/attention_v1.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py`

统计：558 insertions / 61 deletions。没有模型、凭据、token、服务器原始大包、native 环境、性能结果或 P8 raw profiler artifact。

## 4. Pinned vLLM

只读仓库 `/Users/wenqingzhang/Desktop/vllm/vllm`：

- HEAD：`84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- tree：`f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`
- worktree：clean
- `DraftAttentionReadInputs` prototype symbol：absent

未对 vLLM 做任何修改。

## 5. 本地证据与检查

`g1-g5_repair3_local.zip` CRC 全部通过；fixture manifest 原始字节 hash 与冻结值一致。最终 targeted 记录为 **270 passed, 0 failed, 0 skipped**，另有 2 个 subtest pass 与 1 个缺失 `vllm._version` warning。该结果对应最终候选，不与中间 269 passed 日志混淆。

通过项：Ruff、format、targeted Mypy、compileall、diff-check、python-init、forbidden-imports、boolean-context、long-functions、symbolic-meta、logger、已安装的 ruff/codespell/typos hooks、gitleaks。

完整 pre-commit 有界重试仍为：`ENVIRONMENT_BLOCKED_actionlint_dependency_network`。阻塞是 actionlint 的 Go 依赖下载无法访问 `proxy.golang.org`，不是测试 PASS，也没有通过删除/跳过检查来掩盖。

关键合同保持：observer 不 query backend event；snapshot/export 不触碰 device completion；capture layer identity 来自真实 forward；KV-sharing owner 与 executing layer 分离；public Graph Gate 冻结；新 SHA 无设备证据；Host tests 不等于 A3 Graph PASS。

## 6. GitHub 身份、仓库与远端状态

GitHub CLI 已认证：

- login：`LucianWQZ`
- account id：`74153505`
- repository：`LucianWQZ/vllm-ascend`
- visibility：public
- viewer permission：`ADMIN`
- origin：`https://github.com/LucianWQZ/vllm-ascend.git`

发布前/后 API ref 核验：

- `refs/heads/fix/p7x-graph-base-a3-repair3`：absent
- `refs/heads/fix/p7x-graph-base-a3-repair2`：`8198ab7a6df6a163316f5d4ed2126242bbeb4aa8`
- `refs/heads/perf/p7x-draft-window-hotpath`：`1b7215c37d1e3c9d1edac1fc20bcad26917ca251`
- `refs/heads/feature/p7x-nongraph-completion`：`c1c2129aa49ee1de381130729de73124a6ec893a`

未修改后三条 ref。

## 7. 发布尝试与安全处置

执行的唯一普通 push：

```bash
git push --set-upstream origin \
  fix/p7x-graph-base-a3-repair3:fix/p7x-graph-base-a3-repair3
```

结果：约 75 秒后失败：

```text
fatal: unable to access 'https://github.com/LucianWQZ/vllm-ascend.git/':
Failed to connect to github.com port 443 after 75003 ms
```

随后 12 秒 bounded `curl --head https://github.com` 同样在连接阶段超时。认证不需要重做；问题位于 Git transport 网络路径。

### API fallback 的受控失败

为判断是否能通过 GitHub Git Data API 精确发布，执行了只创建对象、不创建 ref 的安全试验：六个 blob、tree、parent、message 均与本地一致，但 GitHub API 将 commit timestamp timezone 规范化为 UTC，生成 commit `f44d4f562154f4532a11b405dab31c61ec6e7f24`，不等于目标 `10cbf4c...`。

脚本在 SHA mismatch 时 hard fail，**未创建目标 branch/ref**。该对象不可达，不是交付提交。没有把它当成成功，也没有继续用 API 覆盖精确历史。

## 8. API 与 clean-room 核验状态

API 可以证明账户、权限、仓库、parent 与目标分支不存在；不能证明未发布的目标 commit/tree 已在 branch 上。

独立 `gh repo clone --branch fix/p7x-graph-base-a3-repair3` 未执行：目标分支不存在是前置阻塞，并且相同 `github.com` Git transport 当前不可达。使用本地对象、worktree、bundle 或 patch 代替 clean-room clone 会违反任务合同，因此没有伪造 clean-room PASS。

恢复 publication 的唯一正确动作：网络恢复后，在仍精确 clean 的候选仓库执行同一条普通 push，再通过 API 和全新 `gh repo clone` 核验 commit/tree/parent/driver hash/clean 状态。不得再次使用 API commit endpoint代替 exact Git object，不得 force push。

## 9. 服务器输入包

生成 `P7X_Graph_Base_A3_Repair3_Server_Input_Pack.zip`，包含 handoff、实现报告、server commands、rerun plan、remaining gates、原始 fixture manifest、`package_repair3_return.py`、README、包内索引和 SHA256SUMS。它不包含模型、token、native 环境、旧服务器大包或 production source；服务器仍必须从 GitHub clean clone exact branch。

由于 publication 未完成，包内 README 和 handoff 明确：`DO_NOT_RUN_UNTIL_PUBLICATION_VERIFIED`，`ready_for_a3_smoke=false`。输入包用于准备和审查，不授权服务器运行。

## 10. 工具限制与设备 Gate

- driver 仍为 `tools/p7x_graph_repair2.py`。
- `--case` 是功能模式；`--case-id` 是实验身份。
- TargetBoundaryProbe 上限 256 条，长 G4 必须预算分组。
- analyze 的 `HOST_CANDIDATE` 不证明 G2 device pass。
- compare-probes 的 head-only PASS 不证明 FULL_TARGET/KV。
- check exit 0 只证明固定 smoke 合同。
- trace-probe 只发现工具，不证明已采集。
- 新 SHA 的 A3 SIGSEGV、G1 actual task operand、G2 device ABA、G3 physical read、G4 S>0/FULL_TARGET、G5 completion/reuse 均未验证。

## 11. Go / No-Go

**NO-GO for Node101/A3 execution now.** 原因只有 publication/clean-room source identity 未闭合。服务器不得用 Notes ZIP 代替 GitHub source，也不得继承旧 SHA 的设备结果。

当且仅当以下全部满足时改为 GO：

1. 普通非 force push 成功；
2. API 显示目标 branch=`10cbf4c...`，tree=`28dddd...`，parent=`8198...`；
3. 全新 `gh repo clone` 从目标 GitHub 恢复相同身份且 clean；
4. driver hash一致；
5. handoff/manifest更新并重新打包校验。

即使完成发布，也只能进入 A3 smoke：`READY_FOR_ALL_G1_G5_CLOSURE=NO`、`NEW_SHA_DEVICE_VERIFICATION=NOT_RUN`、`PUBLIC_GRAPH_GATE=STILL_FROZEN`。
