"""Standalone figures from retained profiling summaries; no model or GPU work."""
from pathlib import Path
import csv,json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;d=json.loads((O/'MRV2_Profiling_Summary.json').read_text());rows=list(csv.DictReader((O/'C15_materialize逐次细分.csv').open()))
fig,axs=plt.subplots(1,2,figsize=(11.5,4.1),layout='constrained')
for pos,(window,color) in enumerate([('OFF','#3264b0'),('ON','#d16b2c')],1):
 v=d['finite_controls'][window]['all_elapsed_ms'];axs[0].scatter([pos-.08,pos,pos+.08],v,color=color,s=38,label=window)
 axs[0].hlines(statistics.median(v),pos-.22,pos+.22,color=color,linewidth=2)
axs[0].set(xticks=[1,2],xticklabels=['Window OFF','Window ON'],ylabel='Active request groups elapsed (ms)',title='C15 long controls: all three process repeats')
axs[0].set_ylim(0,max(d['finite_controls']['ON']['all_elapsed_ms'])*1.15);axs[0].text(.02,.04,'15 requests / 240 tokens / 47 Draft Host replays\nAcceptance unavailable; descriptive data, no speedup claim',transform=axs[0].transAxes,fontsize=8)
x=[int(r['generation']) for r in rows]
axs[1].plot(x,[float(r['outer_ms']) for r in rows],label='Materialize outer',color='#3264b0',linewidth=1.4)
axs[1].plot(x,[float(r['Draft_materialize_exact_length_snapshot_ms']) for r in rows],label='Exact length snapshot',color='#d16b2c',linewidth=1.2)
axs[1].set(xlabel='Recorded generation (Host identity)',ylabel='Host range elapsed (ms)',title='C15 ON-long: 47 materialize observations');axs[1].legend(fontsize=8)
fig.suptitle('MRV2 profiling: retained scopes, not kernel duration or completion proof',fontsize=11)
fig.savefig(O/'Profiling_C15有限重复与materialize.svg');fig.savefig(O/'Profiling_C15有限重复与materialize.png',dpi=150);plt.close(fig)
c=d['diagnostic_comparison_C17']['cases'];names=['PROFILE_ON_short_control','PROFILE_ON_short_normal','PROFILE_LIFE'];v=[c[n]['active_group_elapsed_ms'] for n in names];fig,ax=plt.subplots(figsize=(7.4,4.8));fig.subplots_adjust(bottom=.23,top=.89,left=.12,right=.98);bars=ax.bar(['No profiler','Normal profile','LIFE diagnostic'],v,color=['#798699','#3264b0','#d16b2c']);ax.set_yscale('log');ax.set_ylim(100,80000)
for bar,value in zip(bars,v):ax.text(bar.get_x()+bar.get_width()/2,value*1.12,f'{value:.1f} ms',ha='center',fontsize=9)
ax.set(ylabel='Active request groups elapsed (ms, log scale)',title='C17 matched short workload: one observation per mode');fig.text(.12,.02,'7 requests / 112 tokens / 21 Draft + 12 Target Host replays\nLIFE adds observer, Host serialization and synchronization; no sync-only attribution.',fontsize=8)
fig.savefig(O/'Profiling_C17正常与LIFE诊断.svg');fig.savefig(O/'Profiling_C17正常与LIFE诊断.png',dpi=150);plt.close(fig)
print('two standalone PNG/SVG figures created from actual C15/C17 summaries')
