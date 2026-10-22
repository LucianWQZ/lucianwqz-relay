import json,os,subprocess,time,hashlib
from pathlib import Path
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');S=R/'candidates/C17_native_disclosure/vllm-ascend';RAW=R/'runs/20261022T132626Z_R2/raw';B=RAW/'C17_prepare_02';REPORT=R/'reports/20261022T132626Z_R2'
for name in ['PROFILE_ON_short_normal','PROFILE_LIFE']:
 p=B/name;t=list((p/'trace').rglob('trace_view.json'));o=RAW/'profile_analysis_C17'/name;o.mkdir(parents=True,exist_ok=False);small=REPORT/'profiling_C17'/name;small.mkdir(parents=True,exist_ok=True)
 assert len(t)==1 and json.loads((RAW/'C17_campaign_01'/name/'runner-result.json').read_text())['dependency_satisfied']
 a=['/usr/local/python3.11.10/bin/python','-m','tools.p7x_graph_repair6_trace','--trace',str(t[0]),'--output',str(o/'flow-analysis-module.json')];start=time.time_ns()
 with (o/'parser_module.log').open('w') as f:x=subprocess.run(a,cwd=S,env=dict(os.environ,PYTHONPATH=str(S),TORCH_DEVICE_BACKEND_AUTOLOAD="0",PYTHONDONTWRITEBYTECODE="1"),stdout=f,stderr=subprocess.STDOUT,timeout=180)
 execution=dict(argv=a,returncode=x.returncode,cwd=str(S),start_ns=start,end_ns=time.time_ns(),parser_sha256=hashlib.sha256((S/'tools/p7x_graph_repair6_trace.py').read_bytes()).hexdigest());(o/'parser_execution.json').write_text(json.dumps(execution,indent=2)+'\n');(small/'parser_execution.json').write_text(json.dumps(execution,indent=2)+'\n')
 if x.returncode==0:
  d=json.loads((o/'flow-analysis-module.json').read_text());payload=dict(flow_counts=d['flow_counts'],coverage=d['coverage'],replays=d['replays'][:2],full_table_path=str(o/'flow-analysis-module.json'),source_trace=str(t[0]),scope='actual flow ids and containment; no adjacency/layer/physical-read inference')
  indices=sorted({i for r in d['replays'][:2] for i in r.get('replay_plus_update_flow_indices',[])})
  if isinstance(d.get('flows'),list):payload['referenced_flows']=[dict(index=i,flow=d['flows'][i]) for i in indices[:20]]
  (small/'typical_replay_fragment.json').write_text(json.dumps(payload,indent=2)+'\n')
 print(name,x.returncode,flush=True)
