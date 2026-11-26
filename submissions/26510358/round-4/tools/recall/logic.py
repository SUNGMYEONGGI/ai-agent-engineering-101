from pathlib import Path
import json

def run(a,kit):
 try:
  mode=a.get('mode')
  if mode=='inspect':
   roots=['tools','ops','logs'];out={}
   for root in roots:
    p=Path(root);out[root]=[str(x) for x in p.glob('**/*') if x.is_file() and ('a2a' in str(x).lower() or root=='ops')][:120]
   return {'ok':True,'files':out}
  if mode=='read':
   p=Path(a['path']);assert str(p).startswith(('ops/','tools/'));return {'ok':True,'text':p.read_text(encoding='utf8')[:60000]}
  if mode=='restore':
   src=Path(a['source']);dst=Path(a['dest']);assert str(dst) in ('ops/a2a_v16.py','ops/a2a_v16_test.py') or kit.testing and str(dst).startswith('tmp/test/');assert str(src).startswith(('tools/','ops/','tmp/test/'));dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(src.read_text(encoding='utf8'),encoding='utf8');return {'ok':True}
  w=str(a.get('word','')).lower();out=[]
  if not w:return {'matches':[],'count':0}
  for p in a.get('paths',['logs/react.jsonl','logs/agent-kit.log']):
   try:
    for line in open(p,encoding='utf8'):
     if w in line.lower():out.append({'file':p,'line':line.rstrip()})
   except (OSError,UnicodeError):pass
  return {'matches':out[-50:],'count':len(out)}
 except Exception as e:return {'ok':False,'error':str(e)}