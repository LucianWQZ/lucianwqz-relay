import json,shutil,subprocess,time
from datetime import datetime,timezone
from common_c19 import *
donor=R/'candidates/C15_native/vllm-ascend';manifest=R/'state/R2_C15_RUNTIME_OVERLAY.json';old=json.loads(manifest.read_text());files=[]
for row in old['overlay']:
 src=donor/row['relative_path'];dst=SOURCE/row['relative_path'];assert digest(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert digest(dst)==row['sha256'];files.append(dict(relative_path=row['relative_path'],bytes=dst.stat().st_size,sha256=row['sha256'],donor=str(src)))
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
sha=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip();tree=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD^{tree}'],text=True).strip()
runtime=dict(schema='mrv2-runtime-overlay-v2',prepared_at_utc=datetime.now(timezone.utc).isoformat(),source_sha=sha,source_tree=tree,candidate=str(SOURCE),donor_manifest=dict(path=str(manifest),sha256=digest(manifest)),overlay=files,scope='Same verified C15 ignored native artifacts; C19 Host-only captured single K/V Tensor metadata fix; production subtree unchanged; verified generated _build_info.py retained as build metadata, no old production Python source overwrite',version_selector_disclosure='VLLM_VERSION=0.28.1 compatibility lane only, pinned source still84030bbe; not release assertion',cache_scope='Shared bounded R2 caches; no binary rebuild or shared-stack upgrade')
(R/'state/R2_C19_RUNTIME_OVERLAY.json').write_text(json.dumps(runtime,ensure_ascii=False,indent=2)+'\n')
h=R/'state/R2_C19_HOST_EVIDENCE.json'
e=json.loads((R/'state/R2_C17_HOST_EVIDENCE_02.json').read_text())
e=[row for row in e if row['label']=='graph_quarantine']
for row in e: row['reuse_basis']='C17 historical Host checks; C17 graph_quarantine anchor reused: entire production subtree identical; native diagnostic producer differs; not new C19 quarantine test'
p=R/'reports'/SID/'C18_host_admission_01.log'
e.append(dict(label='local_admission',status='PASS',path=str(p),sha256=digest(p),source_sha='52c3d487bb3c302d7170087aaaa79e34e3de7846',scope='C18 historical admission checks, source unchanged in C19; derived real C17 manifest old/new negative verdict retained'))
p=R/'reports'/SID/'C19_host_native_01.log'
e.append(dict(label='native_fia_binding_safety_and_cli',status='PASS',path=str(p),sha256=digest(p),source_sha=sha,scope='45 actual C19 Host checks; frozen single-Tensor metadata, strict native ABI/geometry/pointers and quarantine guards'))
h.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
a=[PYTHON,'-m','tools.p7x_graph_local_candidate','prepare','--repo',str(SOURCE),'--vllm',str(VLLM),'--inputs',str(R/'inputs/inputs'),'--output',str(PLAN.parent),'--host-evidence',str(h),'--run-id','r2-c19-phy0-20261022T132626Z'];log=R/'reports'/SID/'C19_prepare.log'
with log.open('w') as f:p=subprocess.run(a,env=environment(),cwd=SOURCE,stdout=f,stderr=subprocess.STDOUT,timeout=300)
print('C19_prepare_rc',p.returncode,flush=True);raise SystemExit(p.returncode)
