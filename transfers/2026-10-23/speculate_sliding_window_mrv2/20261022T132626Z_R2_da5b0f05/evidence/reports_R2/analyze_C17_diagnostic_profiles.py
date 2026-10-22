"""Compare predeclared matching short requests; diagnostic total cost, no sync-only claim."""
import json,datetime
from pathlib import Path
from profile_analysis_common import ROOT,RAW,ANALYSIS_ROOT,analyze_case,load
B=RAW/'C17_prepare_02';cases={}
for name in ('PROFILE_ON_short_control','PROFILE_ON_short_normal','PROFILE_LIFE'):
 p=B/name
 assert load(RAW/'C17_campaign_01'/name/'runner-result.json')['dependency_satisfied']
 c=analyze_case(p);c['observer_installation']=load(p/'campaign.json').get('observer_installation','NOT_AVAILABLE');cases[name]=c
normal=cases['PROFILE_ON_short_normal'];life=cases['PROFILE_LIFE'];control=cases['PROFILE_ON_short_control'];keys=['completed_requests','generated_tokens','prompt_token_lengths','observed_draft_graph_replays','observed_target_graph_replays'];same={k:normal[k]==life[k]==control[k] for k in keys}
result=dict(producer_sha='057b8e0300967e68e3f2a78c5910c8877521674e',cases=cases,external_work_comparison=same,comparison_scope='same external request workload; LIFE adds observer/event/sync/D2H and may alter effective diagnostic preparation; difference is not isolated synchronize overhead or normal Window speedup',profiler_timing='initialization/capture and warmup excluded by committed bounded request profile',read_set='NOT_AVAILABLE',normal_reuse='NOT_PROVEN_BY_SERIALIZED_DIAGNOSTIC')
p=ANALYSIS_ROOT/'MRV2_Profiling_Summary.json';d=load(p);history=ANALYSIS_ROOT/'history/MRV2_Profiling_Summary_C15原件.json'
if not history.exists():history.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
d['schema']='mrv2-profile-round2-v2';d['producer_shas']={'C15_long':'1e88c8208670518f63043552b530b1ed3e2f2677','C17_short_diagnostic':result['producer_sha']};d.pop('producer_sha',None);d['diagnostic_comparison_C17']=result;d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(ANALYSIS_ROOT/'C17_诊断与正常对照.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
rows=['## C17短请求正常/诊断对照（本轮新采集）','',f"源码C17 `{result['producer_sha']}`，同一Phy0 TP1。逐次原件`C17_prepare_02/<case>`；两个profile的完整flow表`profile_analysis_C17/<case>/flow-analysis-module.json`，小型典型片段`profiling_C17/<case>`。C17 native参数导出失败不影响这些独立profile；本组三个case的runner/profile-joint均接受。",'', '|case|scope|requests/tokens|Draft/Target replay|elapsed ms|初始化 s|', '|---|---|---:|---:|---:|---:|']
for name,c in cases.items():rows.append(f"|{name}|{c['profiler_scope']}|{c['completed_requests']}/{c['generated_tokens']}|{c['observed_draft_graph_replays']}/{c['observed_target_graph_replays']}|{c['active_group_elapsed_ms']:.3f}|{c['initialization_seconds']:.3f}|")
rows+=['',f'外部有效工作量逐项一致性：`{same}`，字段来自campaign.outputs/profile.calls，非shape猜测。仅各一次短对照，没有足够样本作置信区间或加速率；不与long总时间相除。', '', '### 显式拷贝/同步标签','', '|标签|normal count / summed us|LIFE count / summed us|','|---|---:|---:|']
labels=sorted(set(normal['trace']['selected_event_statistics'])|set(life['trace']['selected_event_statistics']))
for name in labels:
 vals=[]
 for c in (normal,life):
  v=c['trace']['selected_event_statistics'].get(name);vals.append(f"{v['count']} / {v['summed_duration_us']:.3f}" if isinstance(v,dict) else 'NOT_AVAILABLE')
 rows.append('|'+name+'|'+'|'.join(vals)+'|')
rows+=['','类别sum可能包含嵌套等待/跨流重叠，不能加总为端到端停顿；缺显式方向字段为NOT_AVAILABLE，不填0。LIFE的event/sync/D2H与observer、额外诊断准备一起计入总开销，不能将elapsed差全归给某一种同步。','', '### Host范围与真实flow','', '|case|materialize p50/p95 ms|metadata|UPDATE|retire|','|---|---:|---:|---:|---:|']
for name in ('PROFILE_ON_short_normal','PROFILE_LIFE'):
 c=cases[name];v=[]
 for label in ('Draft_materialize','Draft_metadata_bind','Draft_UPDATE_CALL','Draft_retire_host'):
  stat=c['host_statistics'].get(label);v.append(f"{stat['p50_ms']:.6f}/{stat['p95_ms']:.6f}" if stat else 'NOT_AVAILABLE')
 rows.append('|'+name+'|'+'|'.join(v)+'|')
for name in ('PROFILE_ON_short_normal','PROFILE_LIFE'):
 c=cases[name]
 rows+=['',name+' flow（仅Host范围关联，目的地见下节分类）：`'+json.dumps(c['trace']['flow_analysis'],ensure_ascii=False)+'`。','']
rows+=['','正常ON provider/recorder实际安装与enabled字段在Summary.diagnostic_comparison_C17.cases[].observer_installation；LIFE属于DIAGNOSTIC_SERIALIZED，不能作为正常无额外同步路径。二者初始化/capture与请求区间分别保存；设备prefill/decode的完整拆分、acceptance、全部Target verification数仍NOT_AVAILABLE。','', '该对照回答诊断观察的总时序影响，没有关闭正常UPDATE生效代际/backing最后consumer、task执行operand或KV physical-read。Native dump内部参数块D2H与本PROFILE_LIFE是不同开关，不能凭D2H标签把它们当作同一种证据。']
report=ANALYSIS_ROOT/'MRV2_Profiling分析.md';old=report.read_text();marker='## C17短请求正常/诊断对照（本轮新采集）';old=old.split(marker)[0];report.write_text(old.rstrip()+'\n\n'+'\n'.join(rows)+'\n');print(json.dumps(dict(same_work=same,elapsed_ms={n:c['active_group_elapsed_ms'] for n,c in cases.items()},scopes={n:c['profiler_scope'] for n,c in cases.items()}),ensure_ascii=False))
