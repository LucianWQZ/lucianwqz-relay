import subprocess,time,json,sys,os
from datetime import datetime,timezone
from common_c19 import *
e=environment();O=RUN/'probe_phy0_04';O.mkdir(exist_ok=False);tool=SOURCE/'tools/p7x_graph_repair7_device.py';rid='r2-c19-phy0-20261022T132626Z'
x=subprocess.run([PYTHON,str(tool),'inspect','--output',str(O/'inspect.json')],env=e,capture_output=True,text=True,timeout=30);assert x.returncode==0,x.stderr
inv=json.loads((O/'inspect.json').read_text());s=subprocess.run(['npu-smi','info'],capture_output=True,text=True,timeout=10);(O/'resources.txt').write_text(s.stdout+s.stderr);assert s.returncode==0 and 'No running processes found in NPU 0' in s.stdout
now=time.time();a=json.loads(AUTH.read_text());receipt=dict(schema='repair7-user-authorized-device-v1',run_id=rid,source_sha=json.loads(PLAN.read_text())['commit'],source_tree=json.loads(PLAN.read_text())['tree'],case_id='PREPROBE',user_authorization=dict(path=str(AUTH),sha256=digest(AUTH)),issued_at=now,expires_at=min(now+1800,a['deadline_epoch_seconds']),host_phy_id=0,tp=1,allocated_nodes={'/dev/davinci0':inv['nodes']['/dev/davinci0']},namespace=inv['namespace'],boot_id=inv['boot_id'],visibility=inv['visibility'],mapping_evidence=[dict(path=str(O/'inspect.json'),sha256=digest(O/'inspect.json'))],resource_evidence=[dict(path=str(O/'resources.txt'),sha256=digest(O/'resources.txt'))],resource_observed_at=now)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');argv=[str(tool),'probe','--receipt',str(O/'receipt.json'),'--run-id',rid,'--output',str(O/'committed-probe.json')]
body="import runpy,sys,time,json,torch;sys.argv="+repr(argv)+";runpy.run_path(sys.argv[0],run_name='__main__');d=json.load(open("+repr(str(O/'committed-probe.json'))+"));print(json.dumps(dict(value=d['value'],logical_device=torch.npu.current_device())),flush=True);time.sleep(10)"
cmd=[PYTHON,'-c',body];start=time.time_ns();f=(O/'stdout.log').open('w');err=(O/'stderr.log').open('w');p=subprocess.Popen(cmd,env=e,stdout=f,stderr=err);observations=[];observed=None
while p.poll() is None:
 q=subprocess.run(['npu-smi','info'],capture_output=True,text=True,timeout=10);path=O/f'npu_smi_{len(observations):02}.txt';path.write_text(q.stdout+'\nSTDERR\n'+q.stderr);rows=[]
 for line in q.stdout.splitlines():
  fields=[x.strip() for x in line.strip().strip('|').split('|')]
  if len(fields)>=5 and fields[0].split()==['0','0'] and fields[4]==str(p.pid):rows.append(line)
 observations.append(dict(at=datetime.now(timezone.utc).isoformat(),path=str(path),smi_mentions_pid=bool(rows),rows=rows,returncode=q.returncode))
 if rows and observed is None:observed=path
 if time.time_ns()-start>90*10**9:raise RuntimeError('bounded probe timeout; preserve owned PID '+str(p.pid))
 time.sleep(2)
rc=p.wait();f.close();err.close();d=dict(pid=p.pid,argv=cmd,start_ns=start,end_ns=time.time_ns(),rc=rc,visibility='0',stdout=(O/'stdout.log').read_text(),stderr=(O/'stderr.log').read_text(),observations=observations,scope='Committed C19 inspect/probe; ten-second process hold after successful calculation solely for external PID mapping, no additional kernel',committed_result=str(O/'committed-probe.json'))
(O/'probe_result.json').write_text(json.dumps(d,indent=2)+'\n');assert rc==0 and observed is not None,d
(O/'probe_observed_npu_smi.txt').write_bytes(observed.read_bytes());print(json.dumps(dict(result=str(O/'probe_result.json'),pid=p.pid,returncode=rc,observations=sum(x['smi_mentions_pid'] for x in observations),value=json.loads((O/'committed-probe.json').read_text())['value'])))
