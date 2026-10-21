# Repair6 最终发布与服务器准备报告

生成时间：2026-10-21T14:58:53.368583+08:00。

## 最终裁定

PUBLICATION=VERIFIED；CLEAN_ROOM=VERIFIED；READY_FOR_A3_SCOPED=YES_AFTER_PREFLIGHT。
NEW_SHA_DEVICE_VERIFICATION=NOT_RUN；READY_FOR_ALL_G1_G5_CLOSURE=NO；PUBLIC_GRAPH_GATE=STILL_FROZEN。
本任务仅发布已审查候选并重签交付；没有改生产/测试源码、创建提交、改写历史、创建 PR/tag/merge、运行服务器或开启公开 Graph。

## 精确身份及范围

- repository：https://github.com/LucianWQZ/vllm-ascend.git
- branch：fix/p7x-graph-base-a3-repair6
- commit：fd0716c59562f64262672de12e4ae26259908d0b
- tree：125b29bcb8fe501d69b53e185f9ec89075528310
- parent：febc43be3309f6d2cd87f9332cb7e031ebaad001
- pinned vLLM：84030bbe3d74d99bad477a3d2e37a973ccd8865c / tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
- fixture SHA256：1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4
- 两仓开始/结束均 clean；无源码修改。继承 DSpark TP1 / K=query7 / W1024 / block128 / capacity1151，Base [7,14,28] 与 Target4 [7,14,28,32] 分 profile。capacity不是max_model_len。

## 定向审查与证据复用

复用了 review-fix exact-file-hash 绑定的 1007 passed 回归、13项独立红绿测试与静态检查；本次逐文件核对测试清单中28个文件的 SHA256 与最终 checkout 相同，没有重跑整套历史测试。新任务实际执行了最终计划42 case的136条真实 argparse解析、PREPARE --help、历史PRE_PUBLICATION拒绝执行验证和交付解包核验；这些不执行NPU。

|Finding|裁决|旧版RED依据|修复/最终合同|仍有限制|
|---|---|---|---|---|
|F1|ACCEPTED|5 invalid CPU-tensor collections received PASS on febc43; repair6_red_initial.log|continuous-v2 actual/reference operands, complete identity/KV/layer contract, independent W1024/B128 recompute, sequential join|diagnostic serialized only; padding finite/shape/masked writes, not padded hidden numerical equality|
|F2|ACCEPTED|real pinned forward graph/reference differ yet producer did not raise; repair6_red_submission.log|flush failed tensors, NumericMismatch, branch latch; driver exit3; checker/runner fail preserved|current and earlier prefix retained, no next generation|
|F3|ACCEPTED|native reference mutated cache to999, old finally restored1; driver ignored normal/numeric poison|instance SubmissionState, restore only completed reference, 74/no teardown on uncertain work; bounded owned-descendant watchdog|Host native substitutes; real device abort remains NOT_RUN|
|F4|ACCEPTED|natural actual CLI wrote NUMERIC_MISMATCH but exit0|0 scoped accepted /2 OPEN/3 numeric/4 invalid/5 resource/124 timeout; runner read-only status and dependency contract|0 never means all G1-G5 passed|
|F5|ACCEPTED|real Target producer complete prefix+PREPARING tail became INVALID_EVIDENCE|recognize only final uncommitted tail; corrupt completion remains INVALID; earlier FAIL wins and corruption remains separate|frozen full plan never shortened|
|F6|ACCEPTED|sample_limit1 still budgeted11; repair6_red_initial.log|one-arm runtime geometry/prefix, numeric own geometry, per-chunk disk checks, branch launch reserves, pack no-compression bound; no global82GB gate|mmap RSS/model HBM must be measured on A3; reserves not total disk guarantee|
|R6-RF-07|ACCEPTED|actual DSpark.capture failed freeze with empty sink; repair6_red_capture_contract.log|instance collecting scope, latest real callback output, successful capture freeze; failure clears collecting|two production files changed diagnostic seam only; NPU not run|

capture NONE-mode 真实输出引用收集、默认关闭无诊断设备操作、numeric失败停止下一代、不确定native提交隔离退出、PREPARING尾部/完整前缀分别处理、分支资源预算，均已由上述最终文件绑定回归覆盖。本次不新增推测性功能。

Ruff、format、定向Mypy、compile/diff及6个适用独立hook检查沿用原有效PASS。完整pre-commit仍为ENVIRONMENT_BLOCKED：markdownlint依赖安装npm EALLOWGIT，Fetching non-root packages from git has been disabled。它是安装策略限制，不等同GitHub传输网络问题；本次没有修改限制、禁用hook或把完整runner标PASS。历史7项VWN Host backend失败不计PASS，未因发布重复运行无关测试。
Signed-off-by：Lucian <2207456347@qq.com>；git %G?=N，无密码学签名，不称作GPG/SSH签名通过。

## 认证、网络与安全

使用现有gh登录；gh api user确认LucianWQZ，目标full_name和push权限确认。没有再次请求登录，没有读取/保存token。最初受限沙箱gh显示token不可用及API连接失败，提升网络权限后同一既有登录成功；不能据最初消息认定认证失效。
按实际macOS代理设置使用HTTP/HTTPS 127.0.0.1:15236（SOCKS配置15235未用于本次）；命令级代理环境，无持久系统网络/TLS改动。执行gh auth setup-git --hostname github.com衔接凭据助手，这是认证配置而非网络修复。未修改origin。没有使用ssh、关闭TLS或增加postBuffer。
对Repair5设备基线至最终提交的待发布差异检查：均为小型Python源码/测试/工具，无权重、大raw、profiler产物；高置信PAT/私钥模式未命中。完整文件大小与SHA在Audit.json。不宣称这是穷尽所有可能秘密的审计。没有自动加入Notes或模型文件。

## 普通push与远端核验

发布前目标分支不存在；只执行一次：
`git push origin fd0716c59562f64262672de12e4ae26259908d0b:refs/heads/fix/p7x-graph-base-a3-repair6`
退出0。随后ls-remote精确返回目标SHA，GitHub git/commits API的tree、单parent精确匹配。对比发布前后所有heads/tags，除新专用分支外变化0。没有force、其他ref推送、PR、tag或merge。
记录见logs/push.json、commit-api.json、refs-before.json、refs-after.json、Remote_Before/After.json。最后再次核对远端SHA。

## 独立网络恢复

`gh repo clone LucianWQZ/vllm-ascend /var/folders/jg/1291_6m930x__sj1qzy3kdsh0000gn/T/repair6-github-cleanroom-6e95xwxl/vllm-ascend -- --branch fix/p7x-graph-base-a3-repair6 --single-branch --no-tags`
完成后checkout exact SHA，核对SHA/tree/parent/clean、Repair6 parent与d41bb588、Repair5 d0a3fc3d ancestry。工具清单全部文件及生产诊断接口hash与已审查源码相同；无objects/info/alternates。没有使用本地对象、共享clone、bundle或patch。
核验时间：2026-10-21T14:57:05.949492+08:00。API可见与独立网络恢复分别留证，二者都完成才签发VERIFIED。

## 服务器准入与执行顺序

先解压本次POST_PUBLICATION输入包，按COMMANDS.md用实际路径运行PREPARE.py；它核验source/import/tools/pinned vLLM/原fixture/NPU，只生成新attempt计划，不运行模型。模型与调度沿用inputs，不重新找fixture。
1. P0，再A0/A1/B0新SHA执行锚点；A1为预期公开Gate负例。
2. PREFIX_OFF/ON单样本预算、存储、读取；成立后Base和Target4各OFF/ON完整集合。
3. COMPARE必须等待对应双臂都结束尝试；列表位置靠前不代表可以提前执行。partial前缀可独立只读恢复，原失败不被抹除。
4. NUMERIC_TARGET4连续参考与NORMAL_ORDER多代；二者的诊断扰动/完成证据分别记账。
5. 正常control/native OFF/ON short/long profiling；详细profile仅有明确字段目的时执行。LIFE成立后受影响ABORT按计划隔离子进程。
6. committed pack工具打包，再receiver核验，保留完整退出/signal/timeout/partial与所有样本。

42个计划case与136条CLI解析不是设备完成。Base缺Target(4,32)保持expected OPEN，不阻断Target4。完整Target资源不足只阻断对应分支，不恢复全局82GB门；轻量/profiling独立。numeric确认失败后durable保存并停止后续代；native不确定提交退出74，不在进程内恢复复用；ABORT仅73和专用checker可接受。无条件忽略非零退出不允许。

## 仍未闭环

新SHA没有任何设备实验。continuous reference属于DIAGNOSTIC_SERIALIZED；正常无逐代同步的完整连续参考未实现。normal reuse、UPDATE生效代际仍UNPROVEN，task内部operand/physical read仍OPEN/CAPABILITY_GAP；Host return/retirement不证明completion。旧Repair5有效前缀仅属于旧SHA，不升级新SHA。完整Target不降为HEAD_ONLY。公开Graph Gate与全部G1–G5验收标准不变。

## 交付与历史

历史PRE_PUBLICATION六份顶层交付完整保存在 `/Users/wenqingzhang/Desktop/Note/MRV2/g1-g5_repair6_publication_local/archive_pre_publication`，旧review-fix报告/ZIP未修改。新包内handoff与顶层一致，原fixture字节hash不变。服务器只执行Git源码，无覆盖patch。
publication evidence ZIP包含认证身份/权限的无凭据结果、push/clone/ancestry/sourcehash、定向测试复用清单、CLI校验及服务器包核验。下载manifest记录顶层交付bytes/hash，不做自身循环hash。
最终解包/CRC/成员hash/JSON/相对入口/身份一致性结果见Publication_Package_Verification.json；不把本地包检查写作A3预检通过。
