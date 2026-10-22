"""Read-only old NPU data/new fixed checker; no torch_npu or NPU API."""
import json,sys,hashlib
from pathlib import Path
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');S=R/'candidates/C16_native_bind/vllm-ascend';sys.path.insert(0,str(S));from tools.p7x_graph_repair8_task_dump import decode_native_fia
BASE=R/'runs/20261022T132626Z_R2/raw/C15_prepare_01/LIFE_TASK_DUMP';index=json.loads((BASE/'task-dump-index.json').read_text());obs=json.loads((BASE/'partial.json').read_text())['operand_events'];rows=[]
for r in index['records']:
 n,t=r['descriptor'];events=json.loads((BASE/r['path']).read_text());captures=[o for o in obs if o['stage']=='capture_operator' and o['num_tokens']==t]
 for e in events:
  if not e.get('name','').startswith('FusedInferAttentionScore_'):continue
  p=decode_native_fia(e,n);candidates=sorted({o['generation_id'] for o in obs if o['stage']=='update_operator' and o['num_tokens']==t and o['length_values']==p['kv_lengths']});assert candidates==[r['last_life_generation']];assert all(o['length_values']!=p['kv_lengths'] for o in captures);rows.append(dict(descriptor=r['descriptor'],native=p,matching_host_generation_values=candidates,capture_lengths=captures[0]['length_values'],layer_name='NOT_AVAILABLE_C15_DID_NOT_SAVE_CAPTURED_KV_POINTERS',execution_occurrence_generation='UNPROVEN'))
result=dict(producer_commit=index['identity']['source_sha'],checker_commit='154f33d99d6b3c6bf373fcfb1af347ae49b915d5',source_run=str(BASE),result_scope='旧C15 NPU产物的新C16代码只读解码；不是C16 NPU执行',new_device_execution=False,status='FIFTEEN_NATIVE_PARAMETER_ARRAYS_DISTINGUISH_CAPTURE_AND_LAST_UPDATE_VALUES',tasks=rows,task_execution_occurrence='UNPROVEN',normal_update_generation='UNPROVEN',normal_backing_reuse='UNPROVEN',physical_read='UNPROVEN',decoder_sha256=hashlib.sha256((S/'tools/p7x_graph_repair8_task_dump.py').read_bytes()).hexdigest())
(R/'reports/20261022T132626Z_R2/C15_native长度值_C16只读复核.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('old data/new checker tasks',len(rows),'scoped arrays match last values only')
