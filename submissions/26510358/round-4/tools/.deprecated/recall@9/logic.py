from pathlib import Path
import json,time,collections

def load(p):
 out=[]
 try:
  for line in Path(p).read_text(encoding='utf8').splitlines():
   try:out.append(json.loads(line))
   except Exception:pass
 except OSError:pass
 return out

def run(a,kit):
 try:
  mode=a.get('mode')
  if mode=='customer_summary':
   since=float(a.get('since',0)); now=float(a.get('now',time.time())); out=[]
   for x in load(a.get('customer_path','customers.jsonl')):
    if not isinstance(x,dict) or float(x.get('ts',x.get('at',0)))<since or '연결점검' in json.dumps(x,ensure_ascii=False):continue
    r=x.get('reply',{});r=r if isinstance(r,dict) else {'reply':str(r)};d=r.get('data') or {}
    out.append({'at':x.get('ts',x.get('at')),'text':x.get('text',''),'reply':r.get('reply',''),'checkout':bool(d.get('checkout_jwt') or d.get('checkouts'))})
   counts=collections.Counter()
   for x in load(a.get('wanted_path','wanted.jsonl')):
    if isinstance(x,dict) and float(x.get('ts',0))>=now-86400 and x.get('item'):counts[str(x['item'])]+=1
   return {'ok':True,'messages':out[-40:],'wanted':counts.most_common(5)}
  if mode=='inspect':
   roots=['tools','ops','logs'];return {'ok':True,'files':{root:[str(x) for x in Path(root).glob('**/*') if x.is_file() and ('a2a' in str(x).lower() or root=='ops')][:120] for root in roots}}
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