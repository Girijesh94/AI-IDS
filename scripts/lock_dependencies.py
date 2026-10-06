"""Record the installed dependency closure for this application's pinned roots."""
from pathlib import Path
from importlib.metadata import distribution, version
from packaging.requirements import Requirement

roots=['Flask','Flask-SocketIO','waitress','scikit-learn','joblib','numpy','pandas','scapy','pyarrow','pywin32','WMI']
pending=list(roots)
found={}
while pending:
    name=pending.pop()
    dist=distribution(name)
    canonical=dist.metadata['Name']
    if canonical.lower() in found: continue
    found[canonical.lower()]=(canonical,dist.version)
    for line in dist.requires or []:
        requirement=Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate({'extra':''}):
            pending.append(requirement.name)
lines=['# Installed transitive closure; Python 3.14.7, Windows, 2026-09-29.']
for name,ver in sorted(found.values(),key=lambda x:x[0].lower()):
    lines.append(name+'=='+ver+("; sys_platform == 'win32'" if name.lower() in {'pywin32','wmi'} else ''))
Path('requirements-lock.txt').write_text('\n'.join(lines)+'\n')
print('Locked',len(found),'packages')

