"""python3 recompute.py — CPU stdlib only; no pickle, torch or NPU required.
Checks stored output equality, finiteness and ABA. NOT full Graph/Target/KV acceptance.
"""
import hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def digest(data):return hashlib.sha256(data).hexdigest()
def safe(name):
 p=(ROOT/name).resolve();assert p.is_relative_to(ROOT);return p

def tensor(ref):
 raw=safe('tensors/'+ref['path']).read_bytes();assert len(raw)==ref['bytes'] and digest(raw)==ref['sha256'];offset=0
 for chunk in ref['chunks']:
  assert chunk['offset']==offset;data=raw[offset:offset+chunk['bytes']];assert len(data)==chunk['bytes'] and digest(data)==chunk['sha256'];offset+=chunk['bytes']
 assert offset==len(raw)
 dtype=ref['dtype'];width={'torch.bfloat16':2,'torch.int32':4,'torch.int64':8}[dtype];assert math.prod(ref['shape'])*width==len(raw)
 if dtype=='torch.bfloat16':values=[struct.unpack('<f',struct.pack('<I',v[0]<<16))[0] for v in struct.iter_unpack('<H',raw)]
 else:values=[v[0] for v in struct.iter_unpack('<i' if width==4 else '<q',raw)]
 return dict(dtype=dtype,shape=ref['shape'],values=values)

def decode(v):
 if not isinstance(v,dict):return v
 assert len(v)==1
 if 'tensor_ref' in v:return tensor(v['tensor_ref'])
 if 'mapping' in v:
  pairs=[(decode(k),decode(x)) for k,x in v['mapping']];assert len(dict(pairs))==len(pairs);return dict(pairs)
 return [decode(x) for x in v.get('list',v.get('tuple'))]

def main():
 index=json.loads((ROOT/'INDEX.json').read_text());records=[];verdicts=[]
 for item in index['records']:
  raw=safe(item['path']).read_bytes();assert digest(raw)==item['sha256'];r=decode(json.loads(raw));assert r['identity']==item['identity'];assert r['inputs']['input_ids']['dtype']=='torch.int32' and r['inputs']['positions']['dtype']=='torch.int64';assert r['inputs']==r['reference_inputs'];n=r['active']*7*r['graph']['shape'][1];a,b=(r[x]['values'][:n] for x in ['graph','reference']);assert len(a)==len(b)==n and all(map(math.isfinite,a+b));assert r['metrics']['atol']==r['metrics']['rtol']==0.0;maximum=max(abs(x-y) for x,y in zip(a,b));assert maximum==0.0
  verdicts.append(dict(scenario=r['case_identity']['scenario'],generation=r['generation'],epoch=r['epoch'],shape=r['graph']['shape'],max_abs=maximum,finite=True));records.append(r)
 assert [r['case_identity']['scenario'] for r in records]==['A','B','A_prime'];assert records[0]['graph']['values']!=records[1]['graph']['values'];assert records[0]['graph']['values']==records[2]['graph']['values'];assert records[0]['reference']['values']!=records[1]['reference']['values'];assert records[0]['reference']['values']==records[2]['reference']['values']
 return dict(status='PASS_RETAINED_OUTPUT_NUMERIC_AND_ABA_ONLY',producer_commit=index['producer_commit'],samples=verdicts,scope=index['scope'],full_KV_joint='NOT_ASSESSED_BY_COMPACT_PACKET')
if __name__=='__main__':print(json.dumps(main(),indent=2))
