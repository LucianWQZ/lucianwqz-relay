from pathlib import Path
from datetime import datetime,timezone
import json
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');SID='20261022T132626Z_R2';O=R/'reports'/SID;SHA='da5b0f054c4b94362ff3539de911b26b4074052a';TREE='af4519a635d6ccd70646f77195fde18368bdf22b';now=datetime.now(timezone.utc).isoformat();out=R/'return'/f'{SID}_{SHA[:8]}';counts=json.loads((O/'ROUND_COUNTS.json').read_text())['counts'];scope='C19 numeric12/ABA, controlled Target4 paired12, LIFE21, native15 post-drain parameters, fourABORT/four real Python unwind; public Gate frozen'
doc=dict(schema='mrv2-next-session-final-v3',session_id=SID,start_utc='2026-10-22T13:26:26+00:00',deadline_utc='2026-10-22T23:26:26+00:00',start_asia_shanghai='2026-10-22T21:26:26+08:00',deadline_asia_shanghai='2026-10-23T07:26:26+08:00',user_resource_reservation_until_utc='2026-10-23T02:00:00+00:00',resource_extension_did_not_extend_task=True,status='BLOCKED_PLATFORM_DECISION',review_material_ready=True,production_graph_readiness='NOT_ESTABLISHED',public_graph_gate='FROZEN',development=dict(sha=SHA,tree=TREE,dirty=False),running_candidate=None,last_device_candidate=dict(sha=SHA,case='UNWIND_after_completion'),last_key_validated_candidate=dict(sha=SHA,scope=scope),last_full_numeric_sha=SHA,last_full_target_pair_sha=SHA,last_native_parameter_binding_sha=SHA,last_fault_validation_sha=SHA,current_case=None,current_attempt=None,active_model_pids=[],active_runner_pids=[],active_profiler_pids=[],active_monitor_pids=[],release_observed_utc='2026-10-22T18:00:40.421613+00:00',release_evidence=str(R/'runs'/SID/'environment/final_release_check/snapshot.json'),device_work_ended_utc='2026-10-22T17:58:28.200388+00:00',counts=counts,source_root=str(R/'work/vllm-ascend'),candidate_root=str(R/'candidates/C19_native_tensor/vllm-ascend'),vllm_pin=dict(sha='84030bbe3d74d99bad477a3d2e37a973ccd8865c',tree='f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee',path=str(R/'candidates/C2_303ef7fe/vllm')),run_root=str(R/'runs'/SID/'raw'),cache_root='/mnt/wenqing/mrv2_graph_server_dev/'+SID,report_root=str(O),review_root=str(out),uncommitted_source_files=[],last_completed_operation='all20 C19 cases accepted; explicit Target join12 pairs; final case/source/strictJSON/bundle/process review completed; packaging self-check follows',next_minimum_actions=['Read platform questions and five-step normal dependency proof; obtain maintainer confirmation of applicable Runtime/Event/update/partial-commit contract','Acceptance owner decides existing task operand/physical-read evidence and Base/Target4 review scope; no Agent waiver','Reuse complete raw/index rather than repeat identical traces; new experiments only for discriminating hypothesis or code impact','Before any device work verify original deadline/user reservation and live processes; do not auto-reset expired authorization'],blocks=dict(normal_update_generation='SOURCE_CHAIN_SUPPORTED_OWNER_CONTRACT_PENDING',normal_backing_reuse='SOURCE_CHAIN_SUPPORTED_OWNER_CONTRACT_PENDING',task_operand='PARTIAL_POST_DRAIN_PARAMETER_BINDING',physical_read='UNPROVEN',base_full_target='NOT_CLOSED_MISSING_TARGET4_32',other_topologies_features='NOT_REASSESSED_THIS_ROUND'),remote_publication='NOT_PERFORMED',git_bundle=dict(name='MRV2_da5b0f05_from_Repair7.bundle',bytes=57320,sha256='280f0918b4f95f4d7ffe160b9864144fdbe07c7f35b68ef0e9ed4ffe349a468e',prerequisite='7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14',restored_exact_sha_tree=True),snapshot_utc=now,server_selfcheck_is_not_user_receipt=True)
(O/'NEXT_SESSION_HANDOFF.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n');(R/'reports/NEXT_SESSION_HANDOFF.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
text=f'''# 下一会话恢复

## 当前结果

会话{SID}，开发及最后完整设备候选C19 `{SHA}`，tree `{TREE}`，工作区clean；无未提交源码。固定源码`{R}/candidates/C19_native_tensor/vllm-ascend`，不可直接编辑该固定候选；开发树`{R}/work/vllm-ascend`。

C19同SHA已完成20个计划case：P0/fixture/CONFIG/A0/A1/B0、LIFE_TASK_BIND、NUMERIC_SENTINEL、LIFE、完整NUMERIC_TARGET4、PREFIX_OFF/TARGET4_OFF、四ABORT/四Python展开，runner全部接受。显式Target4联合12对；numeric12/ABA通过；15个native参数块逐层关联。前哨、小型CPU复算、完整矩阵、受控Target、串行完成、正常生命周期各自范围分开。

当前状态BLOCKED_PLATFORM_DECISION；代码/证据材料可审查，PRODUCTION_GRAPH_READINESS未建立，public Graph Gate冻结。无push/merge。正常多代合同、task执行operand/physical-read与Base/Target4范围待维护者/验收owner，不靠重复相同trace解决。

## 进程与时间

本任务设备链17:58:28 UTC结束，监督/导航/worker/profiler均退出。18:00:40 UTC核对164个已知PID无本任务残留，NPU0无进程；恢复仍应新查，不能从旧快照推断存活或设备completion。没有活动case可续跑，禁止重启旧campaign来制造新覆盖。

原任务START2026-10-22 13:26:26 UTC，DEADLINE2026-10-22 23:26:26 UTC（北京次日07:26:26），恢复不重置。用户新确认预约实际到北京10月23日10:00，但任务提前截止不变。过期后不能自动初始化NPU；新实验须有有效预约和新鲜mapping/resource/admission。

## 下一条最小动作

先读平台问题单.md、正常UPDATE与backing顺序核验.md及ACCEPTANCE_VERDICTS.json。源码已提供Stars/endGraphNotify、跨代stream/event和Host参数vector寿命的明确推导；需要维护者确认适用合同，owner裁决既定task operand/physical-read方案和Base缺(4,32)支持范围。

如果得到明确新假设/必须代码改动：核对git/进程/剩余窗口→保存反例→改开发树→受影响Host→新本地commit→新固定checkout/runtime/plan→fresh inspect/probe/check/bind→单case。不得修改C19在用源码、覆盖旧attempt、amend已实验提交，或将历史SHA结果改名新候选。没有新判别力时保留raw并审查，不无限采同样dump。

## 路径与环境

raw `{R}/runs/{SID}/raw`；报告`{O}`；本轮唯一交付`{out}`。/mnt/wenqing/.../{SID}仅有限cache/tmp，与NFS是不同文件系统，换目录不能释放同一文件系统空间。quota未知，预算/可写检查见STORAGE_BINDING及资源预算JSON；不恢复旧500GiB门槛，不删历史/权重/他人文件。

实际Python/usr/local/python3.11.10/bin/python，CANN9.1.0、torch_npu2.10.0.post4、vLLM pin84030bbe...不变。运行命令login:false，加载/usr/local/Ascend/ascend-toolkit/set_env.sh，按已批准实际NPU入口处理权限。VLLM_VERSION=0.28.1仅main-lane兼容选择，非发行版声明。必要native和生成_build_info.py从已核验donor恢复，不能用旧业务Python覆盖候选；runtime manifests和实际worker完整10库来源保留。

Phy0的visible0→logical0由probe04 PID/SMI关联；不能把逻辑npu:0当任意宿主Phy0。后八卡未使用，TP16及其他方法/特性本轮未扩展。

## 代码恢复与复查

bundle MRV2_da5b0f05_from_Repair7.bundle，57320 bytes，SHA256 280f0918b4f95f4d7ffe160b9864144fdbe07c7f35b68ef0e9ed4ffe349a468e。需精确Repair7 `7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14`，已在新bare仓库实际verify/fetch并恢复到C19 SHA/tree。仅恢复Git源码，不包含模型/凭据/共享栈或完整native运行环境。

在独立、已有Repair7基线的仓库中先`git bundle verify <bundle>`，再`git fetch <bundle> HEAD:refs/heads/recover-c19`并创建新的worktree；不能hard reset用户工作树。pinned vLLM与runtime overlay按各manifest单独核对。

review中的compact_numeric_C19可用普通python3 recompute.py复算，不用-O、无需torch/NPU/pickle；仅保留输出/输入和ABA，不含完整KV或独立调用证明。大型tensor/trace及完整flow表在服务器raw，按索引追溯。服务器自检不是用户接收端验证。

## 必须保留的失败/边界

C12旧ABORT runner4失败、C17原native单Tensor容器失败、C16 wrapper路径/审批拒绝、早期Host环境失败均未覆盖。外部监督脚本hash是exit时文件hash；Sentinel计数补丁前版本已精确按早期B0 hash恢复，两个快照和审计保留，fixed模型源码/argv未变。

native verbose API同步D2H读的是kernel参数块，ts/dur是合成布局；C19的15task绑定仅post-drain，不是实际replay occurrence或KV physical-read。Base与Target4分开，C6旧profile/C8+C10旧复核仍标原SHA，非C19实测。
'''
(O/'RESUME.md').write_text(text);(R/'reports/RESUME.md').write_text(text);print('final handoff and self-contained resume written, no stale running model fields')
