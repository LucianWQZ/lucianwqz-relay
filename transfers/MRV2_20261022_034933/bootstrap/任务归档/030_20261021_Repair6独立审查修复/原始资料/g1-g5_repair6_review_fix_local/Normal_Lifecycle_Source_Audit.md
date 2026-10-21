# 正常非async MRV2生命周期：源码可证明与未知项

固定vLLM 84030bbe；Ascend绑定本报告最终提交。没有修改该时序。

|操作|owner/stream与顺序|源码位置|可证明/未知|
|---|---|---|---|
|Window物化/graph backing copy_|P3/current stream，五个read carrier copy|draft_window_graph.py::bind_read_carrier 约826|Host同代copy提交；不是完成|
|update_stream.wait_stream(current)|在replay之前record依赖|dflash/aclgraph.py::run_fullgraph|UPDATE等待此前materialize/current工作，不覆盖随后replay|
|captured FIA wait/reset|capture stream ExternalEvent；task group|attention_v1.py::full_graph_fia 约1082|有显式等待点；re-record/reset与task update代际需版本语义|
|super.run_fullgraph → replay|current stream，合法None|pinned cudagraph_utils.py::run_fullgraph|只提交，非设备完成|
|UPDATE begin/FIA.out/end/event.record|独立update_stream|attention_v1.py::update_graph_params 约916–951|Host调用明确使用本代metadata；不能由此认定作用N或N+1|
|greedy/Markov sampling、draft_tokens|captured图后的current-stream依赖|pinned DSpark/DFlash propose|最后Window读者为Draft attention任务；token采样依赖其输出|
|proposal_scope retire/清空live|Host P3 lease finally|draft_window_eager.py:: _draft_window_proposal_scope 约286–374|不是device fence|
|req_states.draft_tokens赋值|current stream，propose返回后|pinned gpu/model_runner.py 2051–2077|同current后续写入通常受stream FIFO；需实际Ascend映射与task语义|
|Target AsyncOutput copy_event|在Draft propose之前创建/record|pinned model_runner.py 2005–2029;async_utils.py 138–168|get_output等待只覆盖Target采样输出，不能直接替代Draft完成|
|DraftTokensHandler|非structured请求set直接返回；get返回-1 placeholders|pinned gpu/spec_decode/utils.py 26–51|普通Base没有额外Draft D2H fence；structured路径才copy_stream.wait/current+event.synchronize|
|EngineCore post_step|非async取draft ids后再调度|pinned engine/core.py 621–628|普通Base可能只取placeholder；Host post_step不等于Draft完成|
|下代同backing copy_|current流继续FIFO|bind_read_carrier；本代Host已retired|若replay及最后reader确在该流，FIFO提供候选HB；外部task/UPDATE跨流仍需证明|

不能因为没有Host同步就判生产race；也不能把Target output event作为已完成证明。尚需确认：当前CANN/torch_npu graph replay任务的stream归属，ExternalEvent reset/record与多次replay的epoch语义，graph_task_update的生效代际及完成含义，update-stream是否仍可能访问本代backing。

最小判别：NUMERIC_TARGET4的串行current/previous reference给诊断代际信息；NORMAL_ORDER保留原提交顺序、有界token copy与最后双stream普通Event drain，收集全部代及reuse地址；normal未加逐代同步。末尾drain不能倒推每次overwrite安全。拿到平台语义后将其与实际task/stream trace闭环，才可能裁决normal-reuse。
没有新增全局同步、双缓冲、UPDATE前移或allocator重写。正常受控、无额外同步的完整连续hidden参考仍缺实现合同，不能从串行诊断PASS推导。
