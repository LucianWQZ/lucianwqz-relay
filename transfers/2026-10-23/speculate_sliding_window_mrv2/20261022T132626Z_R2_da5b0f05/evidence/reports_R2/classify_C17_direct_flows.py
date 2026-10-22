"""Distinguish any flow inside a replay Host range from an actual model execute edge."""
from pathlib import Path
import json,collections
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');O=R/'reports/20261022T132626Z_R2';RAW=R/'runs/20261022T132626Z_R2/raw';results={}
for case in ('PROFILE_ON_short_normal','PROFILE_LIFE'):
 flowpath=RAW/'profile_analysis_C17'/case/'flow-analysis-module.json';d=json.loads(flowpath.read_text());trace=next((RAW/'C17_prepare_02'/case/'trace').rglob('trace_view.json'));doc=json.loads(trace.read_text());events=doc['traceEvents'] if isinstance(doc,dict) else doc;rows=[];counts=collections.Counter()
 for replay in d['replays']:
  fs=[]
  for index in replay['direct_flow_indices']:
   f=d['flows'][index];destination=[dict(event_index=i,name=events[i].get('name'),category=events[i].get('cat'),pid=events[i].get('pid'),tid=events[i].get('tid'),args=events[i].get('args')) for i in f['destination_intervals']]
   model=any(x['name']=='MODEL_EXECUTE' for x in destination)
   counts['flow_to_model_execute' if model else 'flow_to_other']+=1
   fs.append(dict(flow_index=index,key=f['key'],original_event_indices=f['event_indices'],destination_intervals=destination,is_model_execute_edge=model))
  counts['ranges_with_any_flow']+=bool(fs);counts['ranges_with_model_execute_flow']+=any(f['is_model_execute_edge'] for f in fs)
  rows.append(dict(replay_event_index=replay['event_index'],flows=fs))
 results[case]=dict(original_parser_coverage=d['coverage'],classified_counts=dict(counts),replay_ranges=len(rows),replays=rows,source_trace=str(trace),source_flow=str(flowpath),scope='Explicit existing flow endpoints; range containment alone is not model/kernel association; no new NPU or replay generation claim')
(O/'C17_direct_flow_实际目的地分类.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v['classified_counts'] for k,v in results.items()}))
