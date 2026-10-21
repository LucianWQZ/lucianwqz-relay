# Repair5完整Profiling独立分析

读取完整trace_view.json、SQLite，不用前500X sample推断。raw路径/hash、事件index、字段/args、表/列/行数在同名JSON。
trace时间Decimal微秒，Host monotonic_ns独立；flow按cat/name/id或id2/localPID/scope关联，仅唯一s/f接受，一对多/重用/缺失保留。

|Case|events|matched|unmatched|ambiguous|Draft replay|直接flow|manager有flow|
|---|---:|---:|---:|---:|---:|---:|---:|
|PROFILE_LIFE|167462|20504|1|0|21|21|21|
|PROFILE_OFF_long_normal|332917|41365|1|2|47|0|47|
|PROFILE_OFF_short_normal|155659|19685|1|0|21|0|21|
|PROFILE_ON_long_normal|345872|42722|1|0|47|0|47|
|PROFILE_ON_short_normal|162036|20336|1|0|21|0|21|

+normal每个REPLAY_PLUS_UPDATE都有显式flow源关联，ONlong每次32条；单REPLAY_SUBMIT直接0，不能将manager全部kernel归给replay。LIFE直接21/21但额外串行化。summary逐次保留关联；最小fragment覆盖完整manager范围+显式flow目的地，original_event_index可回原trace。
存在async_npu/torch_to_npu、async_task_queue/enqueue_to_dequeue、HostToDevice与Dequeue@acl_memcpy_host_to_device等。task/context/stream可复用，未建立generation唯一关联仍UNRESOLVED_ASSOCIATION，不因缺generation停止所有分析。
long Target(1,8)24/(2,16)6，short6/6。ONlong14条source_start_column>0为Host descriptor事实，不是物理read。control无native。
原control REPLAY_PLUS_UPDATE均值short1.337→2.578ms、long1.228→2.662ms保留。范围含materialize、metadata/bind、wait_stream Hostcall、replay提交、consumer/UPDATE及Host记录，不等于kernel duration，不能把差额归给FIA或UPDATE。
Repair6包真实方法增加materialize/metadata_bind/UPDATE_CALL/retire_host子range，不复制调用、不加D2H/sync/I/O；开销profile与额外shapes/stack详细profile分开，installed signature不支持则CAPABILITY_UNVERIFIED。旧record_shapes=False/with_stack=False不是平台能力缺失。
kernel duration sum与E2E分别报告，跨stream不相加当walltime；kernel未覆盖区间不是全设备idle。无法唯一细分prefill/decode、Target/Draft kernel的部分UNRESOLVED。P-A开销分析有效，不能升级成physical block read或task operand。
