"""Preserve per-sample source/contracts without loading full KV tensor storage."""
from pathlib import Path
import json,csv,hashlib
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');O=R/'reports/20261022T132626Z_R2';B=R/'runs/20261022T132626Z_R2/raw/C19_prepare_01/NUMERIC_TARGET4';m=json.loads((B/'numeric-reference.json').read_text());joint=json.loads((B/'numeric-joint.json').read_text());assert joint['status']=='PASS_DIAGNOSTIC_CONTINUOUS_REFERENCE';rows=[]
def decode(v):
 if not isinstance(v,dict):return v
 if 'tensor_ref' in v:return v
 if 'mapping' in v:return {decode(k):decode(x) for k,x in v['mapping']}
 return [decode(x) for x in v.get('list',v.get('tuple'))]
for item,j in zip(m['samples'],joint['samples'],strict=True):
 p=B/item['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==item['sha256'];sample=decode(json.loads(raw));assert sample['identity']['source_sha']=='da5b0f054c4b94362ff3539de911b26b4074052a';assert (j['generation'],j['epoch'])==(sample['generation'],sample['epoch']);metric=j['metrics'];inputs=sample['inputs'];hidden=sample['hidden_contract'];rows.append(dict(source_sha=sample['identity']['source_sha'],run_id=sample['identity']['run_id'],case_id=sample['identity']['case_id'],generation=j['generation'],epoch=j['epoch'],scenario=j['scenario'],status=j['status'],active=sample['active'],descriptor=json.dumps(sample['descriptor']),input_ids_dtype=inputs['input_ids']['tensor_ref']['dtype'],positions_dtype=inputs['positions']['tensor_ref']['dtype'],output_shape=json.dumps(metric['shape']),output_dtype=metric['dtype'],finite=metric['finite'],max_abs=metric['max_abs'],max_rel=metric['max_rel'],atol=metric['atol'],rtol=metric['rtol'],kv_equal=j['kv_equal'],current_match=j['current_match'],hidden_contract=json.dumps(hidden,ensure_ascii=False),sample_manifest=str(p),manifest_sha256=item['sha256']))
assert len(rows)==12
with (O/'C19_连续数值逐样本结论.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('C19 numeric12 rows saved, exact dtypes/finite/tolerances and current/KV linkage retained')
