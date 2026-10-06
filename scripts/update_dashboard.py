"""Apply compatibility and evidence-display fixes to the existing dashboard."""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]/'frontend'
escape="""function esc(v){return String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));}\n"""
for path in root.glob('*.html'):
    if path.name=='operations.html': continue
    text=path.read_text(encoding='utf-8')
    text=text.replace('http://localhost:5000/api','/api')
    text=text.replace("io('http://localhost:5000',","io(location.origin,")
    if 'function esc(v)' not in text:
        text=text.replace('<script>','<script>\n'+escape,1)
    text=text.replace('href="/attack_tracker.html"','href="/operations"').replace('Attack Tracker</a>','Operations</a>')
    # Strings rendered in template literals must be escaped; numeric fields are schema validated.
    for expr in ["r.reason||'—'", "r.src_ip||'?'", "r.dst_ip||'?'", "(a.reason||'—').substring(0,42)",
                 "log.component || 'SYSTEM'", "log.message || '-'", "log.source || 'system'", "title"]:
        text=text.replace('${'+expr+'}','${esc('+expr+')}')
    text=text.replace("const tpr=(parseFloat(m.tpr||0)*100).toFixed(0);","const tpr=m.tpr==null?null:(parseFloat(m.tpr)*100).toFixed(0);")
    text=text.replace("const fpr=(parseFloat(m.fpr||0)*100).toFixed(0);","const fpr=m.fpr==null?null:(parseFloat(m.fpr)*100).toFixed(0);")
    text=text.replace('width:${tpr}%', 'width:${tpr||0}%').replace('width:${fpr}%', 'width:${fpr||0}%')
    text=text.replace('${tpr}%','${tpr==null?\'—\':tpr+\'%\'}').replace('${fpr}%','${fpr==null?\'—\':fpr+\'%\'}')
    text=text.replace("`Win:${d.window||'—'} Smp:${d.samples_attacks||0}`", "'Live traffic is unlabeled'")
    text=text.replace('SYSTEM ONLINE','API STATUS').replace('Confidence</th>','Model confidence</th>')
    # Health is not a guarantee of active capture or a running model.
    text=text.replace("if (response.ok) document.getElementById('statusText').textContent = 'System Online';", "if(response.ok){const h=await response.json();document.getElementById('statusText').textContent=h.mode+' / '+h.status+' / '+h.ml_mode;}")
    if path.name in ['index.html','network_flows.html']:
        text=text.replace("const d=await jx(`${API}/health`);if(!d)return;", "const d=await jx(`${API}/health`);if(!d){document.getElementById('mlLbl').textContent='OFFLINE';return;}")
        text=text.replace("const mode=(d.ml_mode||'hybrid').toUpperCase();", "const mode=((d.mode||'unknown')+' / '+(d.ml_mode||'unavailable')).toUpperCase();")
        text=text.replace("if(c>10||t>500)setDefcon('critical');", "if(c>0)setDefcon('critical');")
        text=text.replace('SYSTEM ONLINE','API STATUS')
        text=text.replace("const labels={critical:'CRITICAL',high:'HIGH ALERT',medium:'ELEVATED',low:'NORMAL'};", "const labels={critical:'REVIEW CRITICAL',high:'REVIEW ALERTS',medium:'REVIEW',low:'NO ACTIVE SIGNAL'};")
    if path.name=='cmd_history.html':
        start=text.index('        function updateCmdAlertsTable(')
        end=text.index('        function filterCmdAlerts(',start)
        text=text[:start]+'''        function updateCmdAlertsTable(alerts) {
            const tbody=document.getElementById('cmdAlertsBody');tbody.replaceChildren();
            if(!alerts.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='No command observations recorded. Check endpoint collection in Operations.';tr.append(td);tbody.append(tr);return;}
            for(const item of alerts){const tr=document.createElement('tr');for(const value of [new Date(item.timestamp*1000).toLocaleString(),item.severity,item.command,'Unavailable (rules only)',item.reason]){const td=document.createElement('td');td.textContent=value;tr.append(td);}tbody.append(tr);}
        }

'''+text[end:]
    if path.name=='system_logs.html':
        text=text.replace('new Date(log.timestamp)','new Date(log.timestamp*1000)')
        text=text.replace('log.timestamp > oneHourAgoMs','log.timestamp*1000 > oneHourAgoMs')
    path.write_text(text,encoding='utf-8')
