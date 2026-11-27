from pathlib import Path
import json,time,collections

def rows(path):
 try:
  with Path(path).open(encoding='utf8') as f:
   for line in f:
    try:
     x=json.loads(line)
     if isinstance(x,dict):yield x
    except ValueError:continue
 except FileNotFoundError:return

def stamp(x):
 try:return float(x.get('ts',x.get('at',0)))
 except (TypeError,ValueError):return 0

def run(a,kit):
 try:
  mode=a.get('mode','search')
  if mode=='read':
   p=Path(a['path']);s=p.as_posix()
   if p.is_absolute() or '..' in p.parts or not (s in ('harness_check.json','public/catalog.json') or s.startswith(('ops/','tools/'))):raise ValueError('invalid path')
   t=p.read_text(encoding='utf8');off=max(0,int(a.get('offset',0)));n=max(1,min(18000,int(a.get('limit',8000))))
   return {'ok':True,'text':t[off:off+n],'length':len(t)}
  if mode=='customer_summary':
   now=float(a.get('now',time.time()));since=float(a.get('since',0));limit=max(1,min(100,int(a.get('limit',40))));out=collections.deque(maxlen=limit)
   def path(key,default):
    if not kit.testing:return default
    p=Path(a.get(key,default))
    if not p.as_posix().startswith('tmp/test/') or '..' in p.parts:raise ValueError('invalid fixture path')
    return p
   for x in rows(path('customer_path','customers.jsonl')):
    t=x.get('text','')
    if stamp(x)<since or not t or '연결점검' in t:continue
    r=x.get('reply',{});r=r if isinstance(r,dict) else {'reply':str(r)};d=r.get('data') or {}
    out.append({'at':stamp(x),'text':t,'reply':r.get('reply',''),'checkout':bool(x.get('checkout') or d.get('checkout_jwt') or d.get('checkouts'))})
   c=collections.Counter(str(x['item']) for x in rows(path('wanted_path','wanted.jsonl')) if stamp(x)>=now-86400 and x.get('item'))
   return {'ok':True,'messages':list(out),'wanted':c.most_common(5)}
  if mode!='search':raise ValueError('unknown mode')
  word=str(a.get('word','')).lower();out=collections.deque(maxlen=30);count=0
  if word:
   for p in ('logs/react.jsonl','logs/agent-kit.log'):
    try:
     with open(p,encoding='utf8',errors='replace') as f:
      for line in f:
       if word in line.lower():count+=1;out.append({'file':p,'line':line.rstrip()[:3500]})
    except FileNotFoundError:continue
  return {'ok':True,'matches':list(out),'count':count}
 except Exception as e:return {'ok':False,'error':str(e) or type(e).__name__}
