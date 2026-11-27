import httpx,json,time,uuid,datetime,re
from pathlib import Path
from urllib.parse import urlparse
BASE='market.ourolabs.ai'
def exchange(a,k,url,method='GET',body=None,auth=False,timeout=12):
 if k.testing:
  v=a['fixture'][method+' '+urlparse(url).path];return (v['status'],v['json'])
 h={'authorization':'Bearer '+k.token('shop')} if auth else {}
 r=httpx.request(method,url,json=body,headers=h,timeout=timeout,follow_redirects=False)
 return r.status_code,r.json()
def api(a,k,path,method='GET',body=None,auth=False):
 if not re.fullmatch(r'/api/[a-zA-Z0-9_/?&=.%+-]+',path) or '..' in path: raise ValueError('invalid API path')
 if path.split('?')[0] in {'/api/join','/api/bankruptcy'}: raise ValueError('operation not permitted')
 return exchange(a,k,k.market.rstrip('/')+path,method,body,auth)
def records(j,*keys):
 if isinstance(j,list): return j
 for key in keys:
  if isinstance(j.get(key),list):return j[key]
 raise ValueError('unexpected fields: '+str(list(j)))
def stamp(x):
 try:
  n=float(x);return n/1000 if n>1e12 else n
 except (ValueError,TypeError):
  try:return datetime.datetime.fromisoformat(str(x).replace('Z','+00:00')).timestamp()
  except ValueError:return 0

def run(a,k):
 try:
  mode=a.get('mode')
  if mode=='a2a':
   card_url=a.get('card_url')
   if not card_url:
    status,j=api(a,k,'/api/agents'); assert status==200
    row=next(x for x in records(j,'agents','shops','items') if str(a['shop']).casefold() in [str(x.get(f,'')).casefold() for f in ('name','shop','id')]);card_url=row.get('card') or row.get('card_url') or row.get('agent_card') or row.get('url')
   if not isinstance(card_url,str) or not card_url.startswith('https://'):raise ValueError('invalid card URL')
   if not card_url.endswith('.json'):card_url=card_url.rstrip('/')+'/.well-known/agent-card.json'
   status,card=exchange(a,k,card_url); assert status==200
   address=card.get('url') or next((x['url'] for x in card.get('supportedInterfaces',[]) if x.get('url')),None)
   if not isinstance(address,str) or not address.startswith('https://'):raise ValueError('invalid A2A endpoint')
   t=a.get('text') or '안녕하세요, Hermes Shop입니다. 현재 어떤 상품을 얼마에 판매하시는지 알려주실 수 있을까요?'
   status,j=exchange(a,k,address,'POST',{'jsonrpc':'2.0','id':str(uuid.uuid4()),'method':'message/send','params':{'message':{'kind':'message','role':'user','messageId':str(uuid.uuid4()),'parts':[{'kind':'text','text':t}],'metadata':{'from':'Hermes Shop'}}}},timeout=30)
   if status!=200 or 'error' in j:return {'ok':False,'error':j,'http_status':status}
   return {'ok':True,'reply':j.get('result',j)}
  if mode in ('scan','review','metrics','metrics_full'):
   now=float(a.get('now',time.time())); status,j=api(a,k,a.get('ledger_path','/api/ledger'))
   if status!=200:return {'ok':False,'error':j,'http_status':status}
   ledger=records(j,'ledger','settles','entries','rows','items','sales'); shop=k.name
   def ts(x):return stamp(next((x[f] for f in ('at','ts','time','settled_at','created_at','t') if f in x),0))
   def ours(x):return any(str(x.get(f,'')).rstrip('/').casefold() in (shop.casefold(),k.shop_url.rstrip('/').casefold(),k.address('shop').casefold()) for f in ('shop','shop_name','shop_url','seller','wallet'))
   h=[x for x in ledger if now-3600<=ts(x)<=now]; h2=[x for x in ledger if now-7200<=ts(x)<=now]
   today=(int(now)+32400)//86400*86400-32400
   logs=[];p=Path(a.get('customers_path','customers.jsonl'))
   if k.testing: logs=a.get('customer_fixture',[])
   elif p.is_file():
    for line in p.read_text(encoding='utf8').splitlines():
     try: logs.append(json.loads(line))
     except ValueError: pass
   logs=[x for x in logs if now-3600<=ts(x)<=now and not x.get('test') and not x.get('synthetic')]
   inquiries=[x for x in logs if x.get('text') or x.get('message') or x.get('inquiry')]; c=sum(bool(x.get('checkout_jwt') or x.get('checkouts') or x.get('checkout') or x.get('action')=='checkout' or x.get('kind')=='checkout') for x in inquiries)
   out={'ok':True,'m':len(h),'i':len(inquiries),'c':c,'s':sum(ours(x) for x in h),'today':sum(ours(x) and today<=ts(x)<=now for x in ledger)}
   if mode in ('scan','review'):
    from collections import Counter
    out['top']=Counter(x.get('shop') or x.get('shop_name') or '?' for x in h2).most_common(3);out['market_2h']=len(h2)
    for key,path,auth in [('agents','/api/agents',False),('inventory','/api/inventory',True),('forum','/api/forum',False)]:
     try:
      status,v=api(a,k,path,auth=auth)
      if status==200:out[key]=v if key!='inventory' else {'balance':v.get('balance'),'units':len(v.get('units',[]))}
     except Exception:pass
   return out
  path='/api/inventory' if mode in ('inventory','inventory_units') else a.get('path',{'restock':'/api/restock','catalog':'/api/catalog','supply':'/api/supply','chain':'/api/chain'}.get(mode,''))
  method=a.get('method','POST' if 'body' in a else 'GET').upper(); assert method in ('POST','GET')
  s,j=api(a,k,path,method,a.get('body'),a.get('auth',path in ('/api/inventory','/api/supply')))
  if mode=='inventory_units' and s==200:return {'ok':True,'units':[u for u in j['units'] if u.get('sku')==a['sku']]}
  good=200<=s<300 or s==402 and path=='/api/supply' and isinstance(j,dict) and all(x in j for x in ('quote','total','pay','units'))
  return {**(j if isinstance(j,dict) else {'data':j}),'ok':good,'http_status':s,**({'error':j} if not good else {})}
 except Exception as e:return {'ok':False,'error':str(e) or type(e).__name__}
