# MRV2 持续开发阶段总结

更新：2026-10-22T10:07:36.220312+00:00。原五小时窗口05:04:38Z至10:04:38Z（北京时间13:04:38至18:04:38），容量错误恢复没有重置授权。

## 当前结果

- 最新代码C12：`d15a510c2afba62b8a0e37aa574550852079fd13`，tree `e98f21c40345f5785aecd237722c86dd3a266640`；本地干净提交，未远端发布。
- 最近关键设备候选C8：`2c550f267484360802578f340429f95f95299e33`；完整连续数值为C8真实产物+C10检查器只读复核。
- 已记录正式模型启动 24 次（以完成的campaign实际process_id计，含预期A1拒绝和环境启动失败）；NPU短计算探针3次，C2私有FIA fixture另列，均不混入模型数。最终精确清单 `MODEL_CAMPAIGN_INDEX.json`，当前未完成case查current_status。
- 当前状态：WAITING_RESOURCE / None；是否有本任务模型：False。最终进程/设备释放以 `state/FINAL_PROCESS_AUDIT.json` 为准，不从旧日志猜测。

## 本轮怎样推进

1. 从C2/C6现有树和失败产物接续，保留所有提交与attempt；正式执行审批恢复Agent设备可见性。C3–C6修复用户授权输入、PID映射、npu-smi列合同与直接脚本bisect冲突。
2. 历史Repair5/6成功环境揭示CANN Python路径和自定义算子运行产物缺失；只补固定候选隔离overlay、记录hash与实际worker加载来源，没有升级驱动/CANN/torch_npu或改共享安装。
3. C6真实CONFIG、A0、预期GRAPH_FROZEN的A1、B0完成；数值前哨采到A/B/Aprime，checker却强求int64。C7精确修input_ids=int32，31项Host；随后发现冻结DSpark层为非causal，C8精确修该字段，87项Host。旧C6数据复核前哨通过。
4. 固定C8重新真实执行CONFIG/A0/A1/B0/NUMERIC_SENTINEL通过，随后采全12连续数值与12Target ON样本。原C8 checker在active3/padded4拒绝合法query offset；C10按真实内核clamp输入、保留padded FIA合同，26项Host及真实损坏反例通过。完整producer/artifact/launcher/plan联合复核12样本通过，max_abs=max_rel=0，ABA可区分。
5. C9增加显式复用全量NUMERIC_TARGET4受控Target ON的入口，54项Host；不伪造case、不删来源/完整性检查。C10包含它，以独立OFF臂比较，避免重复采集大dump。
6. C6正常profiling四矩阵与四控制已采集并分析，ON-long descriptor最大S列8；materialize是具体Host开销候选。flow只能关联父replay+UPDATE，不能进一步证明task operand/physical read。
7. C1 production异常隔离保持于当前候选；Host证明保留可疑backing并拒绝继续复用。osexit故障点、串行LIFE和正常顺序观察分别记录，不把它们合成正常异步完成证明。

8. C8私有C2 fixture在计算前循环导入DeviceOperator，停止LIFE依赖并保留失败。C11仅预注册Ascend ops，62项Host通过，独立固定候选重新走P0/C2及必要模型链；设备实际结果以C11行裁决，不能继承C8整矩阵。

9. C11私有fixture已越过循环导入，但capture中缺少speculator子模块。C12增加capture前显式加载，14项定向Host通过；C12设备验证未运行。LIFE/ABORT前置仍未满足，不跳过。

## 分项裁决

| 项目 | 结论 |
|---|---|
| REFERENCE_INTEGRITY | PASS_RECEIVE_ADAPTER_ORIGINAL_PUBLICATION_LAYOUT_FAIL_RETAINED |
| SOURCE_AND_IMPORT | PASS_SCOPED_FIXED_C8_WORKER_AND_C10_CHECKER |
| DEVICE_AUTHORIZATION_AND_MAPPING | PASS_PHY0_THIS_SESSION_ONLY |
| REAL_CONFIG_STARTUP | PASS_SCOPED |
| REQUEST_EXECUTION | PASS_A0_A1_B0_SCOPED |
| FULL_TARGET_BASE | NOT_RUN_NEW_SOURCE_KNOWN_MISSING_TARGET_4_32 |
| FULL_TARGET_TARGET4 | SCOPED_TARGET_EXECUTION_AND_NUMERIC_VALID |
| REAL_DRAFT_CONTINUOUS_NUMERIC | PASS_DIAGNOSTIC_CONTINUOUS_REFERENCE |
| ABA_DISCRIMINATION | PASS_SCOPED |
| DIAGNOSTIC_COMPLETION | NOT_RUN_C2_PREREQUISITE_FAILED |
| NORMAL_UPDATE_GENERATION | OPEN_PLATFORM_CONTRACT |
| NORMAL_BACKING_REUSE | OPEN_LAST_NATIVE_CONSUMER |
| ABORT_ISOLATION | NOT_RUN_C2_PREREQUISITE_FAILED |
| PROFILING_COLLECTION | PASS_SCOPED_4_NORMAL_PLUS_4_CONTROL |
| PROFILING_ANALYSIS | DONE_WITH_EXPLICIT_NOT_AVAILABLE |
| MULTI_DEVICE_EXTENSION | NOT_RUN |
| TASK_INTERNAL_OPERAND | OPEN_NOT_AVAILABLE |
| PHYSICAL_READ | OPEN_NOT_AVAILABLE |
| PRODUCTION_GRAPH_READINESS | NOT_READY_FOR_FORMAL_SUPPORT_APPROVAL |
| PUBLIC_GRAPH_GATE | STILL_FROZEN |

每项source/profile/device/evidence/限制见 `ACCEPTANCE_VERDICTS.json`；逐attempt producer/artifact/checker/runner见 `MRV2_实验矩阵与结论.csv`。Base与Target4独立，旧Repair6 Base10/Target4 12对只作历史参考。最新归档状态文档01_当前进展与下一步仍将新Repair7设备列NOT_RUN；本轮新证据按各SHA另列，不推导其他组合全通过。

## 尚缺什么、下一轮最小工作

优先由平台维护者答复UPDATE生效代际、参数地址最后consumer、ExternalEvent和部分提交合同，或审定可区分的native hook；由验收owner明确task operand/physical read证据要求。需要新增依赖时再设计最小production所有权修复并量化性能，不能盲目串行化后称原路径通过。

C11另含fixture启动修复；最终源码尚未同SHA重跑整套连续数值/Target矩阵；本轮C8已有真实产物，C10复核范围明确。若支持审查要求最终同SHA从producer到runner贯通，下一预约在固定C10（或有新production修复的候选）重跑受影响数值锚点/完整矩阵及必要回归。未完成的Target、LIFE/ABORT/NORMAL_ORDER按矩阵恢复，不覆盖旧attempt。新预约必须明确，旧deadline不自动续期。

Graph尚未达到正式支持审查批准条件；可审查代码和软件/设备证据已更具体。public Gate保持冻结。没有push/PR/merge，没有上传public relay，没有reset设备或处理其他用户进程。

## 文件入口与恢复

先看本总结、`MRV2_实验矩阵与结论.csv`、`MRV2_Profiling分析.md`。恢复读`RESUME.md`与`NEXT_SESSION_HANDOFF.json`，先查活动进程和剩余授权。代码根和固定候选在dev/adapt，raw根见`STORAGE_BINDING.json`。本轮Git bundle恢复基线和验证见`04_提交与Bundle恢复_持续开发.md`。大tensor、trace、完整flow表留服务器，审查包只含最小片段及hash/index；服务器自检不是用户接收端验证。
