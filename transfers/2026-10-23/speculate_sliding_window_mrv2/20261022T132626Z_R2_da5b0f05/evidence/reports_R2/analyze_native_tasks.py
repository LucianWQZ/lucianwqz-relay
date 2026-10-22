"""Read-only native JSON analysis. Word equality is not ABI or physical-read proof."""
import json,csv,re,hashlib
from pathlib import Path
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt')
BASE=R/'runs/20261022T132626Z_R2/raw/C15_prepare_01/LIFE_TASK_DUMP';OUT=R/'reports/20261022T132626Z_R2'
index=json.loads((BASE/'task-dump-index.json').read_text());partial=json.loads((BASE/'partial.json').read_text());rows=[]
for item in index['records']:
 desc=item['descriptor'];host=[r for r in partial['operand_events'] if r['num_tokens']==desc[1]]
 expected={r['actual_table_address'] for r in host};assert len(expected)==1
 pointer=expected.pop();layers=sorted({r['layer_name'] for r in host})
 canonical={r['canonical_table_address'] for r in partial['g4_records'] if r['num_tokens']==desc[1]} if all('num_tokens' in r for r in partial['g4_records']) else set()
 native=json.loads((BASE/item['path']).read_text())
 for n,event in enumerate(native):
  if not event['name'].startswith('FusedInferAttentionScore_'):continue
  a=event['args'];words=[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',a.get('Kernel Args',''))]
  pos=[i for i,w in enumerate(words) if w==pointer]
  rows.append(dict(descriptor=str(desc),source_sha=index['identity']['source_sha'],pid=index['identity']['process_id'],native_path=str((BASE/item['path']).relative_to(R)),native_row=n,model_id=a.get('Model Id'),stream_id=a.get('Stream Id'),task_id=a.get('Task Id'),task_type=a.get('Task Type'),kernel_args_bytes=a.get('Kernel Args Size'),parsed_words=len(words),host_table_pointer=hex(pointer),matching_word_indices=str(pos),table_pointer_matches=len(pos),host_layer_candidates=';'.join(layers),layer_assignment='UNPROVEN_NO_LAYER_ID_IN_NATIVE_JSON',parameter_version='UNRESOLVED_CAPTURE_VS_LAST_UPDATE',physical_read='UNPROVEN'))
assert len(rows)==15
with (OUT/'C15_native_FIA参数字关联.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary=dict(source_sha=index['identity']['source_sha'],run='C15_prepare_01/LIFE_TASK_DUMP',scope='READ_ONLY_NATIVE_PARAMETER_WORD_ANALYSIS',descriptors=3,fia_tasks=15,all_match_host_table_word=all(r['table_pointer_matches']==1 for r in rows),word_indices=sorted({r['matching_word_indices'] for r in rows}),host_layer_count=5,layer_assignment='UNPROVEN',native_parameter_version='UNRESOLVED_CAPTURE_VS_LAST_UPDATE',physical_read='UNPROVEN',normal_backing_reuse='UNPROVEN',native_ts_dur='NO_MEASURED_DEVICE_CLOCK_CONTRACT; not used as elapsed or flow')
(OUT/'C15_native_FIA参数字分析.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
