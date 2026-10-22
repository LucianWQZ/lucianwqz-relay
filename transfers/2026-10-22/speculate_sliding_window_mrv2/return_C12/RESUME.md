# 下一会话恢复

原窗口：2026-10-22 05:04:38Z→10:04:38Z（北京13:04:38→18:04:38）。不自动续期；到期不得启动NPU。先读journal/current_status.json、state/FINAL_PROCESS_AUDIT.json并核对实际进程。

最新开发C12 `d15a510c2afba62b8a0e37aa574550852079fd13` / tree `e98f21c40345f5785aecd237722c86dd3a266640`，开发树干净，固定代码 `candidates/C12_fixture/vllm-ascend`。C12仅14项Host验证，尚无NPU；该候选未复制运行二进制、未prepare设备计划。全部本地提交，未发布。

最近关键设备证据C8 `2c550f267484360802578f340429f95f95299e33`：真实CONFIG/A0/A1/B0/NUMERIC_SENTINEL通过；完整NUMERIC_TARGET4采12样本，原checker query padding错误导致runner失败保留；C10 `c8f9a4bbddf33bc4cc02fdfe39f6aad75c6cad4a`只读联合复核12样本通过、ABA可区分，最大误差0。C8 TARGET4_OFF完整12样本已完成，与NUMERIC_TARGET4的真实ON臂用C10显式join通过12对。不是新C10/C12 NPU运行。C8 NORMAL_ORDER限定检查通过，不证明正常backing完成。

C6（本轮local SHA 1c920c3669b76f301ff9472650ceb0e842ccf03c，不是旧Repair6）正常profiling OFF/ON×short/long四采集及四控制全部通过并分析；ON-long实际S列最大8。完整flow表留服务器，直接replay flow关联0，父replay+UPDATE不可拆分；无task operand/physical read。

最新C11 `8bdc2e2f20ac8d71aecacfe8567ae695681a797b`设备CONFIG/A0/A1通过，B0未运行。C8 C2私有fixture先因DeviceOperator循环导入失败；C11预注册ops后进入capture但缺speculator子模块；C12显式加载它，Host14项通过。两次fixture失败原件保留。LIFE与4个ABORT因C2前置未通过，本轮NOT_RUN，不能跳过。C1异常quarantine仍仅Host功能证据，不能把osexit或进程退出当设备completion。

下一条最小动作：取得新有效预约，给C12固定checkout复制并逐项核验既有runtime overlay（C8/C11 donor与二进制hash），新run/attempt目录prepare、inspect/probe/check/bind；先P0/C2验证启动修复。若通过，再CONFIG/A0/A1/B0/LIFE/ABORT；最终同SHA数值/Target回归按影响与验收要求安排。不要覆盖C8/C11产物，不修改运行候选，不把新提交伪装GitHub VERIFIED。

实际Python `/usr/local/python3.11.10/bin/python`，login:false，source CANN set_env.sh，固定PYTHONPATH含pinned vLLM与CANN Python/TBE。旧/home/wenqing venv editable会导向旧源码。当前受管工具设备与/mnt/wenqing写入须正式require_escalated；不得改全局安全配置。代码ROOT `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt`，raw `/mnt/wenqing/mrv2_graph_server_dev/20261022T0640Z_C2_recovery`。空间逐case重测，不能使用未分配/mnt/weight目录。

维护者决策：正常UPDATE生效代际、backing最后consumer/覆盖合同、未知native部分提交；验收owner决策task内部operand/physical read证据。public Graph Gate冻结；完整分项见ACCEPTANCE_VERDICTS.json。恢复bundle以精确Repair7为前置，见04_提交与Bundle恢复_持续开发.md及state/BUNDLE_VERIFY_C12.json。
