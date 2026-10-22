import json,shutil,subprocess
from common_c13 import *
old=json.loads((R/'state/R2_C12_RUNTIME_OVERLAY.json').read_text()); files=[]
for row in old['overlay']:
 src=R/'candidates/C12_fixture/vllm-ascend'/row['relative_path'];dst=SOURCE/row['relative_path'];assert digest(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert digest(dst)==row['sha256'];files.append(dict(row,donor=str(src)))
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
sha=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip();tree=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD^{tree}'],text=True).strip()
old.update(source_sha=sha,source_tree=tree,candidate=str(SOURCE),overlay=files,abi_scope='Same verified C12 binary files; C13 changes Python diagnostic tools only; not a universal ABI assertion')
(R/'state/R2_C13_RUNTIME_OVERLAY.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
e=json.loads((R/'state/R2_C12_HOST_EVIDENCE.json').read_text());p=R/'reports'/SID/'C13_host_05.log';e.append(dict(label='real_c1_unwind_and_abort_runner',status='PASS',path=str(p),sha256=digest(p),source_sha=sha,scope='69 targeted Host checks; source changes tools only; new device execution pending'));h=R/'state/R2_C13_HOST_EVIDENCE.json';h.write_text(json.dumps(e,indent=2)+'\n')
a=[PYTHON,'-m','tools.p7x_graph_local_candidate','prepare','--repo',str(SOURCE),'--vllm',str(VLLM),'--inputs',str(R/'inputs/inputs'),'--output',str(PLAN.parent),'--host-evidence',str(h),'--run-id','r2-c13-phy0-20261022T132626Z'];log=R/'reports'/SID/'C13_prepare.log'
with log.open('w') as f:p=subprocess.run(a,env=environment(),cwd=SOURCE,stdout=f,stderr=subprocess.STDOUT,timeout=300)
print('C13_prepare_rc',p.returncode,flush=True);raise SystemExit(p.returncode)
