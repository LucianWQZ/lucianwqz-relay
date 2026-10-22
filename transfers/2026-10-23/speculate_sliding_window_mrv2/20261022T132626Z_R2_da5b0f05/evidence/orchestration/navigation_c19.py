"""One bounded Markdown writer for an existing model chain; never modifies JSON state."""
import datetime,json,os,pathlib,subprocess,time
R=pathlib.Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');J=R/'journal';SID='20261022T132626Z_R2';OUT=R/'runs'/SID/'environment';deadline=json.loads((R/'state/ROUND2_USER_AUTHORIZATION_RECORD.json').read_text())['deadline_epoch_seconds'];candidates=[]
for name in pathlib.Path('/proc').iterdir():
 if not name.name.isdigit():continue
 try:
  args=(name/'cmdline').read_bytes().split(b'\0')
  if len(args)>1 and pathlib.Path(args[1].decode(errors='replace')).name=='c19_campaign.py':candidates.append(int(name.name))
 except OSError:pass
assert len(candidates)==1,candidates
pid=candidates[0];ticks=pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19];meta=dict(pid=os.getpid(),watched_chain_pid=pid,watched_start_ticks=ticks,maximum_deadline_epoch=deadline,start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Markdown snapshot only; heartbeat not business progress')
(OUT/'navigation_C19_monitor.json').write_text(json.dumps(meta,indent=2)+'\n')
try:
 while time.time()<deadline:
  try:
   if pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]!=ticks:break
  except OSError:break
  s=json.loads((J/'current_status.json').read_text());d=s.get('development',{});now=datetime.datetime.now(datetime.timezone.utc).isoformat();text=f'''# 第二轮当前进展（快照 {now}）

- 当前开发SHA：`{d.get('sha')}`；未提交修改：{d.get('dirty')}；tree `{d.get('tree')}`。
- 当前case：`{s.get('current_case')}`；阶段 `{s.get('status')}`；动作：{s.get('current_action')}。
- 实际runner PID：{s.get('runner_pid')}；实际worker PID：{s.get('model_worker_pids')}；设备观察：{s.get('npu_observation')}。
- 上个结束case：{s.get('last_completed_case')}；最近runner结论：{s.get('runner_status')}。None表示当前case尚无最终结论。
- 最新生产者样本进展（不是联合验收）：{(s.get('durable_samples') if s.get('last_model_progress') and str(s.get('model_phase_source','')).startswith('durable producer manifests:') else '当前case没有可关联的持久样本计数')}。
- 最后业务日志进展：{s.get('last_model_progress')}；外部监控检查：{s.get('last_monitor_check')}；Agent/case调度更新：{s.get('last_agent_update')}。本Markdown刷新不替代业务进展。

## 已确认与仍缺什么

C15已真实完成私有FIA fixture、CONFIG/A0/A1/B0、完整12数值/ABA、Target4双臂12对、21代LIFE、四ABORT及四真实Python展开；最近完整设备候选C15 1e88c8208670518f63043552b530b1ed3e2f2677。六个long控制与三组正常profiling已采集。C19正在重验关键锚点和新增native参数绑定；不同SHA不拼成一个PASS。

正常UPDATE/backing的条件依赖顺序已有源码和匹配CANN9.1依据；仍需native多代完成/版本合同。原生15个FIA task观察到Window carrier地址字及匹配安装kernel资料，未关闭完整task内部绑定或physical read。public Graph Gate冻结。

## 当前窗口、路径和下一步

本轮开发窗口固定2026-10-22 13:26:26–23:26:26 UTC；用户新确认资源可用至10月23日02:00 UTC，但本轮提前停止，不延长任务。窗口，北京21:26:26–次日07:26:26；恢复和资源等待不延长。用户已确认16芯片释放，本轮主线仅Phy0 TP1。源码{R}/work/vllm-ascend，固定C19在candidates/C19_native_tensor/vllm-ascend，raw {R}/runs/{SID}/raw。本地/mnt/wenqing目录仅缓存。

当前队列：P0/C2/CONFIG/A0/A1/B0→LIFE_TASK_BIND→前哨/LIFE→完整数值和Target4→四ABORT/四真实Python展开；profile沿用未受变更影响的C17采集。依赖失败只停相关分支，原失败attempt保留。

查看：journal/progress.log、journal/current_status.json、reports/RESUME.md；决策reports/{SID}/DECISION_QUEUE.md；本轮矩阵和profiling分析在reports/{SID}/。本快照不从进程存活推断kernel执行或验收PASS。
''';p=J/'00_当前进展.md';tmp=p.with_suffix('.md.navpartial');tmp.write_text(text);tmp.replace(p);time.sleep(30)
finally:
 meta.update(end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit='WATCHED_CHAIN_EXIT_OR_DEADLINE');(OUT/'navigation_C19_monitor.json').write_text(json.dumps(meta,indent=2)+'\n');print('navigation monitor ended',os.getpid(),flush=True)
