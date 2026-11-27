import httpx,json,time,uuid,re,statistics
from pathlib import Path
from collections import Counter,defaultdict
from urllib.parse import urlparse

def req(a,k,url,method='GET',body=None,auth=False,timeout=12):
 if k.testing:
  v=a['fixture'][method+' '+urlparse(url).path+('?' + urlparse(url).query if urlparse(url).query else '')];return v['status'],v['json']
 h={'Authorization':'Bearer '+k.token('shop')} if auth else {};r=httpx.request(method,url,json=body,headers=h,timeout=timeout,follow_redirects=False)
 try:return r.status_code,r.json()
 except ValueError:return r.status_code,{'error':r.text[:300]}
def api(a,k,p,method='GET',body=None,auth=False):
 if not re.fullmatch(r'/api/[a-zA-Z0-9_/?&=.%+\-]+',p) or '..' in p or p.split('?')[0]=='/api/join':raise ValueError('invalid path')
 return req(a,k,k.market.rstrip('/')+p,method,body,auth)
def rows(j,*keys):
 if isinstance(j,list):return j
 for key in keys:
  if isinstance(j.get(key),list):return j[key]
 raise ValueError('unexpected response fields')
def ledger(a,k):
 acc=[];cursor=-5000
 for _ in range(20):
  s,j=api(a,k,'/api/ledger?after='+str(cursor))
  if s!=200:raise ValueError('ledger HTTP '+str(s))
  page=rows(j,'entries','ledger');acc.extend(page)
  if not page:break
  n=max((x.get('seq',0) for x in page),default=0)
  if n<=cursor:break
  cursor=n
 return acc
def stamp(x):
 try:return float(x.get('ts',x.get('at',0)))
 except (TypeError,ValueError):return 0
def norm(x):return str(x or '').rstrip('/').lower()
def run(a,k):
 try:
  mode=a.get('mode')
  if mode=='a2a':
   u=a.get('card_url')
   if not u:
    s,j=api(a,k,'/api/agents');assert s==200
    row=next(x for x in rows(j,'agents','shops','items') if norm(a['shop']) in [norm(x.get(f)) for f in ('name','shop','id')]);u=row.get('card') or row.get('card_url') or row.get('agent_card') or row.get('url')
   if not isinstance(u,str) or not u.startswith('https://'):raise ValueError('invalid card URL')
   if not u.endswith('.json'):u=u.rstrip('/')+'/.well-known/agent-card.json'
   s,c=req(a,k,u);assert s==200
   endpoint=c.get('url') or next((x['url'] for x in c.get('supportedInterfaces',[]) if x.get('url')),None)
   if not isinstance(endpoint,str) or not endpoint.startswith('https://'):raise ValueError('invalid endpoint')
   text=a.get('text') or '안녕하세요, Hermes Shop입니다. 지금 어떤 상품을 얼마에 판매하시나요?'
   body={'jsonrpc':'2.0','id':str(uuid.uuid4()),'method':'message/send','params':{'message':{'kind':'message','role':'user','messageId':str(uuid.uuid4()),'parts':[{'kind':'text','text':text}],'metadata':{'from':'Hermes Shop'}}}}
   s,j=req(a,k,endpoint,'POST',body,timeout=30)
   if s!=200 or 'error' in j:return {'ok':False,'error':j,'http_status':s}
   return {'ok':True,'reply':j.get('result',j)}
  if mode in ('metrics','metrics_full','scan','review'):
   now=float(a.get('now',time.time()));l=ledger(a,k);ss=[x for x in l if x.get('kind')=='settle' and x.get('round',4)==4 and stamp(x)<=now+10];own=lambda x:norm((x.get('data') or {}).get('shop_url') or (x.get('data') or {}).get('shop')) in (norm(k.shop_url),norm(k.name));h=[x for x in ss if stamp(x)>=now-3600];h2=[x for x in ss if stamp(x)>=now-7200];day=now-((now+32400)%86400)
   logs=a.get('customer_fixture',[]) if k.testing else []
   if not k.testing:
    try:
     for line in Path('customers.jsonl').read_text(encoding='utf8').splitlines():
      try:logs.append(json.loads(line))
      except ValueError:pass
    except FileNotFoundError:pass
   inquiries=[x for x in logs if now-3600<=stamp(x)<=now+10 and x.get('text') and '연결점검' not in json.dumps(x,ensure_ascii=False)]
   def checkout(x):
    r=x.get('reply') or {};d=r.get('data') or {} if isinstance(r,dict) else {};return bool(x.get('checkout') or x.get('checkout_jwt') or d.get('checkout_jwt') or d.get('checkouts'))
   out={'ok':True,'m':len(h),'i':len(inquiries),'c':sum(checkout(x) for x in inquiries),'s':sum(own(x) for x in h),'today':sum(own(x) and stamp(x)>=day for x in ss),'last_seq':max((x.get('seq',0) for x in l),default=0),'market_2h':len(h2)}
   if mode in ('scan','review'):
    s,shops=api(a,k,'/api/shops');s2,board=api(a,k,'/api/board');s3,forum=api(a,k,'/api/forum');s4,inv=api(a,k,'/api/inventory',auth=True)
    if s!=200 or s2!=200:raise ValueError('shops or board failed')
    shoprows=rows(shops,'shops','agents');lookup={norm(x.get('url')):x.get('name') for x in shoprows};cnt=Counter(lookup.get(norm((x.get('data') or {}).get('shop')), (x.get('data') or {}).get('shop','?')) for x in h2)
    prices=defaultdict(list)
    for x in h2:
     d=x.get('data') or {};p=d.get('amount');
     if d.get('sku') and d.get('grade') and isinstance(p,(int,float)):prices[(d['sku'],d['grade'])].append(p)
    out.update({'top':cnt.most_common(3),'shops':shops,'board':board,'forum':forum if s3==200 else None,'balance':inv.get('balance') if s4==200 else None,'inventory_count':len(inv.get('units',[])) if s4==200 else None,'medians':[{'sku':x[0],'grade':x[1],'median':statistics.median(v),'count':len(v)} for x,v in prices.items()]})
   return out
  path='/api/inventory' if mode in ('inventory','inventory_units') else a.get('path',{'restock':'/api/restock','catalog':'/api/catalog','supply':'/api/supply','chain':'/api/chain'}.get(mode,''));method=a.get('method','POST' if 'body' in a else 'GET').upper()
  if method not in ('POST','GET'):raise ValueError('invalid method')
  s,j=api(a,k,path,method,a.get('body'),a.get('auth',path in ('/api/inventory','/api/supply')))
  if mode=='inventory_units' and s==200:return {'ok':True,'units':[u for u in j['units'] if u.get('sku')==a['sku']]}
  good=200<=s<300 or s==402 and path=='/api/supply' and isinstance(j,dict) and all(x in j for x in ('quote','total','pay','units'))
  return {**(j if isinstance(j,dict) else {'data':j}),'ok':good,'http_status':s,**({'error':j} if not good else {})}
 except Exception as e:return {'ok':False,'error':str(e) or type(e).__name__}
