import subprocess
from common_c17 import *
args=[PYTHON,'-m','tools.p7x_graph_local_candidate','prepare','--repo',str(SOURCE),'--vllm',str(VLLM),'--inputs',str(R/'inputs/inputs'),'--output',str(PLAN.parent),'--host-evidence',str(R/'state/R2_C17_HOST_EVIDENCE_02.json'),'--run-id','r2-c17-phy0-20261022T132626Z']
with (R/'reports'/SID/'C17_prepare_02.log').open('w') as f:
 p=subprocess.run(args,env=environment(),cwd=SOURCE,stdout=f,stderr=subprocess.STDOUT,timeout=300)
print('prepare02_rc',p.returncode,flush=True)
raise SystemExit(p.returncode)
