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

