"""Explicit same-thread containment and existing flow ids; no clock mixing."""
import json,collections,bisect,statistics
from decimal import Decimal
from pathlib import Path
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');RAW=R/'runs/20261022T132626Z_R2/raw';REPORT=R/'reports/20261022T132626Z_R2';case='PROFILE_ON_long_materialize';p=next((RAW/'C15_prepare_01'/case/'trace').rglob('trace_view.json'));d=json.loads(p.read_text());events=d['traceEvents'] if isinstance(d,dict) else d;label='repair5/Draft_materialize_exact_length_snapshot';parents={i:e for i,e in enumerate(events) if e.get('ph')=='X' and e.get('name')==label};threads=collections.defaultdict(list)
for i,e in parents.items():threads[(e.get('pid'),e.get('tid'))].append((Decimal(str(e['ts'])),Decimal(str(e['ts']))+Decimal(str(e['dur'])),i))
for key,v in threads.items():v.sort()
starts={k:[x[0] for x in v] for k,v in threads.items()};stats=collections.defaultdict(list);child_by_parent=collections.defaultdict(list)
for i,e in enumerate(events):
 if e.get('ph')!='X' or i in parents or (e.get('pid'),e.get('tid')) not in threads:continue
 key=(e.get('pid'),e.get('tid'));t=Decimal(str(e['ts']));ix=bisect.bisect_right(starts[key],t)-1
 if ix<0:continue
 a,b,parent=threads[key][ix]
 if a<=t and t+Decimal(str(e['dur']))<=b:
  stats[e['name']].append(float(e['dur']));child_by_parent[parent].append(dict(index=i,name=e['name'],cat=e.get('cat'),duration_us=e['dur']))
flowpath=RAW/'profile_analysis_C15'/case/'flow-analysis-module.json';flows=json.loads(flowpath.read_text())['flows'];matched=[];destinations=collections.Counter()
for i,flow in enumerate(flows):
 linked=set(flow.get('host_ranges',[]))&set(parents)
 if not linked:continue
 names=[events[k].get('name') for k in flow.get('destination_intervals',[])];destinations.update(names);matched.append(dict(flow_index=i,flow=flow,parent_indices=sorted(linked),destination_names=names))
longest=max(parents,key=lambda i:float(parents[i]['dur']));summary=dict(case=case,source_trace=str(p),source_flow_table=str(flowpath),snapshot_count=len(parents),same_thread_nested_statistics={k:dict(count=len(v),sum_us=sum(v),p50_us=statistics.median(v),max_us=max(v)) for k,v in sorted(stats.items(),key=lambda kv:sum(kv[1]),reverse=True)},matched_flow_count=len(matched),matched_destination_counts=dict(destinations),longest_snapshot=dict(index=longest,event=parents[longest],children=sorted(child_by_parent[longest],key=lambda x:float(x['duration_us']),reverse=True)[:18]),interpretation='nested durations are not additive; original snapshot includes existing synchronization/backlog plus copy; no Host monotonic ns subtraction, no kernel-name/adjacency generation inference')
(REPORT/'C15_snapshot_trace分析.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');(REPORT/'profiling_C15/PROFILE_ON_long_materialize/snapshot_flow_fragment.json').write_text(json.dumps(dict(source_trace=str(p),full_flow_table=str(flowpath),selected_flows=matched[:4]),ensure_ascii=False,indent=2)+'\n');print('snapshots',len(parents),'flows',len(matched),'top_names',list(summary['same_thread_nested_statistics'])[:8])
