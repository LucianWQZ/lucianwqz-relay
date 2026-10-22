"""R2 finite repeats + materialize nesting; preserve all runs and missing fields."""
import csv,json,statistics
from pathlib import Path
from profile_analysis_common import analyze_case,load,union_duration,RAW,ANALYSIS_ROOT
from collections import defaultdict
from decimal import Decimal
BASE=RAW/'C15_prepare_01';cases={}
for path in sorted(BASE.glob('*')):
 if not ((path.name.startswith('PERF_') or path.name.startswith('PROFILE_')) and (path/'profile.json').exists() and (path/'campaign.json').exists()):continue
 c=analyze_case(path);campaign=load(path/'campaign.json');c['observer_installation']=campaign.get('observer_installation','NOT_AVAILABLE');c['scope']='C15 new real NPU run; scope from profile.json: '+c['profiler_scope'];cases[path.name]=c
summary=dict(schema='mrv2-profile-round2-v1',producer_sha='1e88c8208670518f63043552b530b1ed3e2f2677',raw_root=str(RAW),cases=cases,old_C6_evidence='HISTORICAL_ONLY: return/MRV2_Profiling分析.md and C6_long逐请求历史统计.csv',normal_update_generation='UNPROVEN_NATIVE_CONTRACT_PENDING',physical_read='UNPROVEN')
controls={}
for window in ['OFF','ON']:
 selected=[cases.get(f'PERF_{window}_long_{i:02}') for i in range(1,4)];valid=[c for c in selected if c]
 v=[c['active_group_elapsed_ms'] for c in valid]
 controls[window]=dict(expected_campaigns=3,observed=len(v),all_elapsed_ms=v,median_ms=statistics.median(v) if v else 'NOT_AVAILABLE',minimum_ms=min(v) if v else 'NOT_AVAILABLE',maximum_ms=max(v) if v else 'NOT_AVAILABLE',sample_standard_deviation_ms=statistics.stdev(v) if len(v)>1 else 'NOT_AVAILABLE',statistics_scope='finite descriptive independent process repeats; shared caches and run order preserved; no speedup/significance claim')
summary['finite_controls']=controls
pairs=[]
for i in range(1,4):
 a,b=(cases.get(f'PERF_{x}_long_{i:02}') for x in ['OFF','ON'])
 if a and b:pairs.append(dict(repetition=i,same_counted_work=all(a[k]==b[k] for k in ['completed_requests','generated_tokens','observed_draft_graph_replays','observed_target_graph_replays','prompt_token_lengths']),OFF_ms=a['active_group_elapsed_ms'],ON_ms=b['active_group_elapsed_ms'],workload_completeness='Acceptance and all Target verifications NOT_AVAILABLE; not a causal Window acceleration ratio'))
summary['paired_descriptive_work']=pairs
p=BASE/'PROFILE_ON_long_materialize/profile.json'
if p.exists():
 doc=load(p);calls={c['call_id']:c for c in doc['calls'] if c.get('active') and c.get('call_id') is not None};rows=[];children=defaultdict(list)
 for c in calls.values():children[c['parent_call_id']].append(c)
 for c in calls.values():
  if c['label']!='Draft_materialize':continue
  child=children[c['call_id']];covered=union_duration([(Decimal(max(v['start_ns'],c['start_ns'])),Decimal(min(v['end_ns'],c['end_ns']))) for v in child]);total=c['end_ns']-c['start_ns'];assert covered<=total
  row=dict(call_id=c['call_id'],generation=c.get('generation'),epoch=c.get('mapping_epoch'),request_group=c['request_group'],outer_ms=total/1e6,direct_children_union_ms=covered/1e6,unmarked_host_residual_ms=(total-covered)/1e6)
  for v in child:row[v['label']+'_ms']=row.get(v['label']+'_ms',0)+(v['end_ns']-v['start_ns'])/1e6
  rows.append(row)
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (ANALYSIS_ROOT/'C15_materialize逐次细分.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 stats={}
 for name in fields:
  if not name.endswith('_ms'):continue
  values=sorted(r[name] for r in rows if name in r)
  stats[name]=dict(samples=len(values),mean_ms=statistics.mean(values),p50_ms=statistics.median(values),p95_ms=values[min(len(values)-1,int(len(values)*.95))],max_ms=max(values))
 summary['materialize_decomposition']=dict(samples=len(rows),statistics=stats,method='Host monotonic ns only; direct child interval union, nested workspace not double counted',nested_statistics=doc['host_statistics'],timing_instrumentation='default-off Host wrappers/record_function; no new synchronization/D2H/query; timings include existing waits, cannot assign all snapshot time to copy device duration')
else:summary['materialize_decomposition']={'status':'NOT_RUN_OR_INCOMPLETE'}
(ANALYSIS_ROOT/'MRV2_Profiling_Summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (ANALYSIS_ROOT/'C15_profile逐请求.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['case','source_sha','group','elapsed_ms']);w.writeheader();w.writerows(dict(case=n,source_sha=c['source']['source_sha'],group=g['label'],elapsed_ms=g['elapsed_ms']) for n,c in cases.items() for g in c['group_times'])
print(json.dumps(dict(cases=len(cases),controls=controls,materialize=summary['materialize_decomposition'].get('statistics','NOT_READY')),ensure_ascii=False))
