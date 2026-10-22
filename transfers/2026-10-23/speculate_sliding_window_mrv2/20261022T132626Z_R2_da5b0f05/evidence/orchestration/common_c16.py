import hashlib,json,os
from pathlib import Path
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt')
SESSION=json.loads((R/'state/ROUND2_SESSION.json').read_text());SID=SESSION['session_id'];RUN=Path(SESSION['run_root']);CACHE=Path(SESSION['cache_root'])
SOURCE=R/'candidates/C16_native_bind/vllm-ascend';VLLM=R/'candidates/C2_303ef7fe/vllm';PYTHON='/usr/local/python3.11.10/bin/python';AUTH=R/'state/ROUND2_USER_AUTHORIZATION_RECORD.json';PLAN=RUN/'C16_prepare_01/case-plan.json'
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def environment():
 e=os.environ.copy();e.update(ASCEND_RT_VISIBLE_DEVICES='0',PYTHONPATH=f'{SOURCE}:{VLLM}:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe',PYTHONDONTWRITEBYTECODE='1',VLLM_USE_V2_MODEL_RUNNER='1',VLLM_VERSION='0.28.1',VLLM_ENABLE_V1_MULTIPROCESSING='0',VLLM_CACHE_ROOT=str(CACHE/'cache/vllm'),TORCH_NPU_CACHE_DIR=str(CACHE/'cache/torch_npu'),ASCEND_CACHE_PATH=str(CACHE/'cache/ascend'),HF_HOME=str(CACHE/'cache/hf'),TMPDIR=str(CACHE/'tmp'))
 e.pop('ASCEND_VISIBLE_DEVICES',None)
 for k in ('VLLM_CACHE_ROOT','TORCH_NPU_CACHE_DIR','ASCEND_CACHE_PATH','HF_HOME','TMPDIR'):Path(e[k]).mkdir(parents=True,exist_ok=True)
 return e
