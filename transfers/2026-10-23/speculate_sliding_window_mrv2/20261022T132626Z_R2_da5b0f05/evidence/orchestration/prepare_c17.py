import json,shutil,subprocess,time
from datetime import datetime,timezone
from common_c17 import *
donor=R/'candidates/C15_native/vllm-ascend';manifest=R/'state/R2_C15_RUNTIME_OVERLAY.json';old=json.loads(manifest.read_text());files=[]
for row in old['overlay']:
 src=donor/row['relative_path'];dst=SOURCE/row['relative_path'];assert digest(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert digest(dst)==row['sha256'];files.append(dict(relative_path=row['relative_path'],bytes=dst.stat().st_size,sha256=row['sha256'],donor=str(src)))
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
sha=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip();tree=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD^{tree}'],text=True).strip()
runtime=dict(schema='mrv2-runtime-overlay-v2',prepared_at_utc=datetime.now(timezone.utc).isoformat(),source_sha=sha,source_tree=tree,candidate=str(SOURCE),donor_manifest=dict(path=str(manifest),sha256=digest(manifest)),overlay=files,scope='Same verified C15 ignored native artifacts; C17 only opt-in post-LIFE Host metadata and native checker; no old Python overwrite',version_selector_disclosure='VLLM_VERSION=0.28.1 compatibility lane only, pinned source still84030bbe; not release assertion',cache_scope='Shared bounded R2 caches; no binary rebuild or shared-stack upgrade')
(R/'state/R2_C17_RUNTIME_OVERLAY.json').write_text(json.dumps(runtime,ensure_ascii=False,indent=2)+'\n')
p=R/'reports'/SID/'C17_host_01.log';h=R/'state/R2_C17_HOST_EVIDENCE.json';h.write_text(json.dumps([dict(label='native_fia_binding_safety_and_cli',status='PASS',path=str(p),sha256=digest(p),source_sha=sha,scope='33 affected Host checks; C16 broader88 historical; disclosure/manifest delta only')],indent=2)+'\n')
a=[PYTHON,'-m','tools.p7x_graph_local_candidate','prepare','--repo',str(SOURCE),'--vllm',str(VLLM),'--inputs',str(R/'inputs/inputs'),'--output',str(PLAN.parent),'--host-evidence',str(h),'--run-id','r2-c17-phy0-20261022T132626Z'];log=R/'reports'/SID/'C17_prepare.log'
with log.open('w') as f:p=subprocess.run(a,env=environment(),cwd=SOURCE,stdout=f,stderr=subprocess.STDOUT,timeout=300)
print('C17_prepare_rc',p.returncode,flush=True);raise SystemExit(p.returncode)
