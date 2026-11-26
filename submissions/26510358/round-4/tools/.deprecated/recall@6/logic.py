import os
from pathlib import Path
def run(a,kit):
 if a.get('mode')=='backup':
  src=Path(a.get('source','tools/a2a_handler/logic.py'));dest=Path(a.get('dest','ops/a2a_v11.py'))
  if kit.testing:
   if src.parts[:2]!=('tmp','test') or dest.parts[:2]!=('tmp','test'):raise ValueError('invalid test path')
  elif str(src)!='tools/a2a_handler/logic.py' or str(dest)!='ops/a2a_v11.py':raise ValueError('invalid path')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(src.read_text(encoding='utf8'),encoding='utf8');return {'ok':True,'bytes':dest.stat().st_size}
 w=str(a.get('word','')).lower();out=[]
 if not w:return {'matches':[],'count':0}
 for p in a.get('paths',['logs/react.jsonl','logs/agent-kit.log']):
  try:
   with open(p,encoding='utf8') as f:
    for line in f:
     if w in line.lower():out.append({'file':p,'line':line.rstrip()})
  except (OSError,UnicodeError):pass
 return {'matches':out[-50:],'count':len(out)}
