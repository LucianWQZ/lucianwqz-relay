"""Copy only actual output/input sample tensors, preserving original manifests/hashes."""
import hashlib,json,shutil
from pathlib import Path
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');SOURCE=R/'runs/20261022T132626Z_R2/raw/C19_prepare_01/NUMERIC_SENTINEL';OUT=R/'reports/20261022T132626Z_R2/compact_numeric_C19';OUT.mkdir(exist_ok=False);(OUT/'tensors').mkdir()
m=json.loads((SOURCE/'numeric-reference.json').read_text());records=[]
campaign=json.loads((SOURCE/'campaign.json').read_text());joint=json.loads((SOURCE/'numeric-joint.json').read_text());assert campaign['identity']['source_sha']=='da5b0f054c4b94362ff3539de911b26b4074052a' and joint['status']=='PASS_NUMERIC_SENTINEL_ONLY'
fields={'identity','generation','epoch','case_identity','descriptor','active','inputs','reference_inputs','graph','reference','metrics','status','hidden_contract'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy_tensors(value):
 if isinstance(value,dict):
  if 'tensor_ref' in value:
   ref=value['tensor_ref'];src=SOURCE/m['tensor_root']/ref['path'];assert src.stat().st_size==ref['bytes'] and digest(src)==ref['sha256'];dest=OUT/'tensors'/ref['path']
   if not dest.exists():shutil.copyfile(src,dest)
  else:
   for v in value.values():copy_tensors(v)
 elif isinstance(value,list):
  for v in value:copy_tensors(v)
for i,s in enumerate(m['samples']):
 raw=SOURCE/s['path'];assert digest(raw)==s['sha256'];doc=json.loads(raw.read_text());subset={'mapping':[[k,v] for k,v in doc['mapping'] if k in fields]};copy_tensors(subset);name=f'sample-{i:03}.json';(OUT/name).write_text(json.dumps(subset,indent=2)+'\n');records.append(dict(path=name,sha256=digest(OUT/name),source_manifest=s['path'],source_manifest_sha256=s['sha256'],identity=s['identity']))
(OUT/'INDEX.json').write_text(json.dumps(dict(scope='Independent CPU recomputation of retained output numeric metrics and A/B/A-prime only; full KV/metadata/launcher joint acceptance requires original server artifacts',producer_commit=m['header']['identity']['source_sha'] if 'identity' in m['header'] else 'da5b0f054c4b94362ff3539de911b26b4074052a',source_root=str(SOURCE),tensor_root='tensors',records=records,omitted='Full pre/post KV checkpoints and full runtime metadata, intentionally not in compact packet',original_joint_sha256=digest(SOURCE/'numeric-joint.json')),ensure_ascii=False,indent=2)+'\n')
print('compact_bytes',sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()))
