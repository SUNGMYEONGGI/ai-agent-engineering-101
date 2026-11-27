from pathlib import Path
import json,time,collections,traceback,uuid

def load(p):
 out=[]
 try:
  for line in Path(p).read_text(encoding='utf8').splitlines():
   try: out.append(json.loads(line))
   except Exception: pass
 except OSError: pass
 return out

def run(a,kit):
 try:
  mode=a.get('mode')
  if mode=='read':
   p=Path(a['path']);s=str(p)
   if p.is_absolute() or '..' in p.parts or not (s=='harness_check.json' or s.startswith(('ops/','tools/'))): raise ValueError('invalid path')
   text=p.read_text(encoding='utf8');off=max(0,int(a.get('offset',0)));limit=max(1,min(8000,int(a.get('limit',8000))))
   return {'ok':True,'text':text[off:off+limit],'length':len(text)}
  if mode=='customer_summary':
   now=float(a.get('now',time.time())); since=float(a.get('since',0));out=[]
   for x in load(a.get('customer_path','customers.jsonl')):
    if not isinstance(x,dict) or float(x.get('ts',x.get('at',0)))<since or '연결점검' in json.dumps(x,ensure_ascii=False):continue
    r=x.get('reply',{});r=r if isinstance(r,dict) else {'reply':str(r)};d=r.get('data') or {}
    out.append({'at':x.get('ts',x.get('at')),'text':x.get('text',''),'reply':r.get('reply',''),'checkout':bool(d.get('checkout_jwt') or d.get('checkouts'))})
   counts=collections.Counter(str(x['item']) for x in load(a.get('wanted_path','wanted.jsonl')) if isinstance(x,dict) and float(x.get('ts',0))>=now-86400 and x.get('item'))
   return {'ok':True,'messages':out[-40:],'wanted':counts.most_common(5)}
  if mode=='inspect':return {'ok':True,'files':{r:[str(p) for p in Path(r).glob('**/*') if p.is_file() and ('a2a' in str(p).lower() or r=='ops')][:120] for r in ['tools','ops','logs']}}
  if mode=='stage_test':
   root=Path('tmp/test')/('stage_'+uuid.uuid4().hex);root.mkdir(parents=True);logic=a['logic'];test=a['test'];(root/'logic.py').write_text(logic,encoding='utf8');(root/'test.py').write_text(test,encoding='utf8')
   ns={};exec(compile(logic,'staged_logic.py','exec'),ns);ts={};exec(compile(test,'staged_test.py','exec'),ts)
   class K:
    testing=True
    def __getattr__(self,k):return getattr(kit,k)
    def sign_jwt(self,obj,role):
     assert role=='shop'
     return 'fixture.jwt.signature'
    def token(self,role):return 'fixture'
   ts['test'](ns['run'],K());return {'ok':True,'stage':str(root),'result':'passed'}
  word=str(a.get('word','')).lower();out=[]
  if not word:return {'matches':[],'count':0}
  for p in a.get('paths',['logs/react.jsonl','logs/agent-kit.log']):
   try:
    for line in open(p,encoding='utf8'):
     if word in line.lower():out.append({'file':p,'line':line.rstrip()})
   except (OSError,UnicodeError):pass
  return {'matches':out[-50:],'count':len(out)}
 except Exception as e:return {'ok':False,'error':str(e) or type(e).__name__,'trace':traceback.format_exc()[-2500:]}