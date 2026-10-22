# 下一会话恢复

## 当前结果

会话20261022T132626Z_R2，开发及最后完整设备候选C19 `da5b0f054c4b94362ff3539de911b26b4074052a`，tree `af4519a635d6ccd70646f77195fde18368bdf22b`，工作区clean；无未提交源码。固定源码`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/C19_native_tensor/vllm-ascend`，不可直接编辑该固定候选；开发树`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/work/vllm-ascend`。

C19同SHA已完成20个计划case：P0/fixture/CONFIG/A0/A1/B0、LIFE_TASK_BIND、NUMERIC_SENTINEL、LIFE、完整NUMERIC_TARGET4、PREFIX_OFF/TARGET4_OFF、四ABORT/四Python展开，runner全部接受。显式Target4联合12对；numeric12/ABA通过；15个native参数块逐层关联。前哨、小型CPU复算、完整矩阵、受控Target、串行完成、正常生命周期各自范围分开。

当前状态BLOCKED_PLATFORM_DECISION；代码/证据材料可审查，PRODUCTION_GRAPH_READINESS未建立，public Graph Gate冻结。无push/merge。正常多代合同、task执行operand/physical-read与Base/Target4范围待维护者/验收owner，不靠重复相同trace解决。

## 进程与时间

本任务设备链17:58:28 UTC结束，监督/导航/worker/profiler均退出。18:00:40 UTC核对164个已知PID无本任务残留，NPU0无进程；恢复仍应新查，不能从旧快照推断存活或设备completion。没有活动case可续跑，禁止重启旧campaign来制造新覆盖。

原任务START2026-10-22 13:26:26 UTC，DEADLINE2026-10-22 23:26:26 UTC（北京次日07:26:26），恢复不重置。用户新确认预约实际到北京10月23日10:00，但任务提前截止不变。过期后不能自动初始化NPU；新实验须有有效预约和新鲜mapping/resource/admission。

## 下一条最小动作

先读平台问题单.md、正常UPDATE与backing顺序核验.md及ACCEPTANCE_VERDICTS.json。源码已提供Stars/endGraphNotify、跨代stream/event和Host参数vector寿命的明确推导；需要维护者确认适用合同，owner裁决既定task operand/physical-read方案和Base缺(4,32)支持范围。

如果得到明确新假设/必须代码改动：核对git/进程/剩余窗口→保存反例→改开发树→受影响Host→新本地commit→新固定checkout/runtime/plan→fresh inspect/probe/check/bind→单case。不得修改C19在用源码、覆盖旧attempt、amend已实验提交，或将历史SHA结果改名新候选。没有新判别力时保留raw并审查，不无限采同样dump。

## 路径与环境

raw `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261022T132626Z_R2/raw`；报告`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/reports/20261022T132626Z_R2`；本轮唯一交付`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/return/20261022T132626Z_R2_da5b0f05`。/mnt/wenqing/.../20261022T132626Z_R2仅有限cache/tmp，与NFS是不同文件系统，换目录不能释放同一文件系统空间。quota未知，预算/可写检查见STORAGE_BINDING及资源预算JSON；不恢复旧500GiB门槛，不删历史/权重/他人文件。

实际Python/usr/local/python3.11.10/bin/python，CANN9.1.0、torch_npu2.10.0.post4、vLLM pin84030bbe...不变。运行命令login:false，加载/usr/local/Ascend/ascend-toolkit/set_env.sh，按已批准实际NPU入口处理权限。VLLM_VERSION=0.28.1仅main-lane兼容选择，非发行版声明。必要native和生成_build_info.py从已核验donor恢复，不能用旧业务Python覆盖候选；runtime manifests和实际worker完整10库来源保留。

Phy0的visible0→logical0由probe04 PID/SMI关联；不能把逻辑npu:0当任意宿主Phy0。后八卡未使用，TP16及其他方法/特性本轮未扩展。

## 代码恢复与复查

bundle MRV2_da5b0f05_from_Repair7.bundle，57320 bytes，SHA256 280f0918b4f95f4d7ffe160b9864144fdbe07c7f35b68ef0e9ed4ffe349a468e。需精确Repair7 `7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14`，已在新bare仓库实际verify/fetch并恢复到C19 SHA/tree。仅恢复Git源码，不包含模型/凭据/共享栈或完整native运行环境。

在独立、已有Repair7基线的仓库中先`git bundle verify <bundle>`，再`git fetch <bundle> HEAD:refs/heads/recover-c19`并创建新的worktree；不能hard reset用户工作树。pinned vLLM与runtime overlay按各manifest单独核对。

review中的compact_numeric_C19可用普通python3 recompute.py复算，不用-O、无需torch/NPU/pickle；仅保留输出/输入和ABA，不含完整KV或独立调用证明。大型tensor/trace及完整flow表在服务器raw，按索引追溯。服务器自检不是用户接收端验证。

## 必须保留的失败/边界

C12旧ABORT runner4失败、C17原native单Tensor容器失败、C16 wrapper路径/审批拒绝、早期Host环境失败均未覆盖。外部监督脚本hash是exit时文件hash；Sentinel计数补丁前版本已精确按早期B0 hash恢复，两个快照和审计保留，fixed模型源码/argv未变。

native verbose API同步D2H读的是kernel参数块，ts/dur是合成布局；C19的15task绑定仅post-drain，不是实际replay occurrence或KV physical-read。Base与Target4分开，C6旧profile/C8+C10旧复核仍标原SHA，非C19实测。
