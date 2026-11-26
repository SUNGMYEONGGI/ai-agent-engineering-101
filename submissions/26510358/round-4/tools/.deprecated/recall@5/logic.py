import json,os
from pathlib import Path
def run(a,kit):
 if a.get('mode')=='list':
  p=Path(a.get('path','.'));return {'path':str(p),'items':[str(x) for x in p.iterdir()][:100]}
 if a.get('mode')=='read':
  p=Path(a['path']);s=p.read_text(encoding='utf8');off=int(a.get('offset',0));return {'total':len(s),'text':s[off:off+int(a.get('length',5000))]}
 w=str(a.get('word','')).lower();out=[]
 if not w:return {'matches':[],'count':0}
 for p in a.get('paths',['logs/react.jsonl','logs/agent-kit.log']):
  try:
   with open(p,encoding='utf8') as f:
    for line in f:
     if w in line.lower():out.append({'file':p,'line':line.rstrip()})
  except (OSError,UnicodeError):pass
 return {'matches':out[-50:],'count':len(out)}
