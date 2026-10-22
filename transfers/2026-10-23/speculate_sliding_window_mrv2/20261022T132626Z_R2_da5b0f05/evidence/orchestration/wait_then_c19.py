"""Wait for this task's C17 chain, then start one bounded fixed C19 chain."""
import json,os,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from common_c19 import *
O=R/'runs'/SID/'orchestration';E=R/'runs'/SID/'environment';m=json.loads((E/'navigation_C17_monitor.json').read_text());pid=m['watched_chain_pid'];ticks=m['watched_start_ticks'];deadline=json.loads(AUTH.read_text())['deadline_epoch_seconds'];start=time.monotonic();state=R/'state/R2_C19_START_SUPERVISION.json';records=dict(supervisor_pid=os.getpid(),wait_for_c17_pid=pid,wait_for_start_ticks=ticks,source_sha='da5b0f054c4b94362ff3539de911b26b4074052a',deadline_epoch=deadline,started_utc=datetime.now(timezone.utc).isoformat(),phase='WAITING_FOR_OWN_C17_CHAIN',purpose='never overlap normal profiling or edit a running candidate');last=0
def note(text):
 with (R/'journal/progress.log').open('a') as f:f.write(datetime.now(timezone.utc).isoformat()+'：'+text+'\n')
def save():state.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
save();note('C19准备完成，等待本任务C17全部独立LIFE/profile自然结束；不取消当前模型，不并发正常profiling。')
while True:
 try:alive=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]==ticks
 except OSError:alive=False
 if not alive:break
 if time.time()>deadline-3600 or time.monotonic()-start>1800:records.update(phase='NOT_STARTED_BOUNDED_WAIT_EXPIRED');save();note('C19未启动：有界等待或剩余预算不满足，保留已完成C15/C17。');raise SystemExit(3)
 if time.monotonic()-last>=30:
  records.update(last_wait_check_utc=datetime.now(timezone.utc).isoformat(),c17_chain_alive=True);save();note('C19资源等待心跳：C17执行链仍存活，具体业务进展读当前case；本等待不算模型进展。');last=time.monotonic()
 time.sleep(10)
assert not (R/'state/R2_C19_CAMPAIGN.json').exists(),'C19 already has a ledger; inspect before resuming'
assert not (RUN/'admission_C19_attempt01').exists(),'C19 admission exists; no duplicate launch'
records.update(phase='FRESH_C19_PROBE',c17_chain_ended_observed_utc=datetime.now(timezone.utc).isoformat());save();note('C17执行链已退出，开始fresh C19 committed inspect/probe04及Phy0 PID映射，再逐case设备准入。')
with (E/'C19_probe_launcher.log').open('w') as f:p=subprocess.run([PYTHON,str(O/'probe_c19_fresh.py')],stdout=f,stderr=subprocess.STDOUT,timeout=180)
records['probe_returncode']=p.returncode;save()
if p.returncode:records.update(phase='BLOCKED_PROBE_FAILED');save();note('C19 probe04失败，未启动模型，见environment/C19_probe_launcher.log');raise SystemExit(p.returncode)
records.update(phase='C19_DEVICE_CHAIN');save()
p=subprocess.Popen([PYTHON,str(O/'c19_campaign.py')]);records['chain_pid']=p.pid;records['chain_start_ticks']=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19];save();children=[]
for script in ('navigation_c19.py','capture_c19_provenance.py'):
 f=(E/(script+'.launcher.log')).open('w');child=subprocess.Popen([PYTHON,str(O/script)],stdout=f,stderr=subprocess.STDOUT);f.close();children.append(child);records[script+'_pid']=child.pid
save();rc=p.wait();records.update(phase='CHAIN_ENDED_RECORDING_COMPLETE_NOT_AUTOMATIC_PASS',chain_outer_rc=rc,ended_utc=datetime.now(timezone.utc).isoformat());save();note('C19执行链已结束，外层rc='+str(rc)+'只描述编排退出；各case须读runner/joint与原始首因，不自动宣布Graph通过。')
# Monitors have their own chain/deadline bounds; do not kill model/worker processes.
for child in children:
 try:child.wait(timeout=40)
 except subprocess.TimeoutExpired:records[str(child.pid)+'_monitor_status']='STILL_WITHIN_ITS_DECLARED_BOUND_CHECK_ON_RESUME'
save();raise SystemExit(rc)
