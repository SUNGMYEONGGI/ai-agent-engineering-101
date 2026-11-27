import json,time,statistics,uuid
from pathlib import Path
from collections import defaultdict,Counter
from urllib.parse import urlsplit
import httpx

def norm(v):return str(v or '').rstrip('/').lower()
def rows(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):return x.get('entries',x.get('ledger',[]))
 return []
def request(kit,path,auth=False,method='GET',body=None):
 if not isinstance(path,str) or not path.startswith('/api/') or path.startswith('//'):raise ValueError('invalid API path')
 r=httpx.request(method.upper(),kit.market.rstrip('/')+path,headers={'Authorization':'Bearer '+kit.token('shop')} if auth else {},json=body,timeout=12,follow_redirects=False)
 try:b=r.json()
 except Exception:b={'text':r.text[:300]}
 return r.status_code,b
def req(kit,path,auth=False):
 s,b=request(kit,path,auth)
 if s!=200:raise ValueError(path+' HTTP '+str(s))
 return b
def items(x,key):return x.get(key,[]) if isinstance(x,dict) else x if isinstance(x,list) else []
def stamp(x):
 try:return float(x.get('ts',x.get('at',0)))
 except (ValueError,TypeError):return 0
def sc(ledger,shops,board,catalog):
 ss=items(shops,'shops');bb=items(board,'shops');byurl={norm(s.get('url')):s.get('name') for s in ss if isinstance(s,dict)}
 counts=Counter();sales=defaultdict(list);names={};times=[]
 for r in rows(ledger):
  if not isinstance(r,dict) or r.get('kind')!='settle' or r.get('round',4)!=4:continue
  d=r.get('data') or {};u=norm(d.get('shop_url') or d.get('shop'));counts[byurl.get(u) or d.get('shop') or '?']+=1
  sku=d.get('sku') or (d.get('item') if isinstance(d.get('item'),str) else (d.get('item') or {}).get('sku'));g=d.get('grade');p=d.get('amount',d.get('price'))
  if sku and g and isinstance(p,(int,float)) and p>0:sales[(sku,g)].append(p);names[sku]=d.get('name','') or names.get(sku,'')
  if stamp(r):times.append(stamp(r))
 top=[{'sku':s,'grade':g,'name':names.get(s,''),'count':len(ps),'median':statistics.median(ps)} for (s,g),ps in sorted(sales.items(),key=lambda x:(-len(x[1]),x[0]))[:15]]
 ls=[]
 for x in catalog.get('items',[]):
  ps=sales.get((x.get('sku'),x.get('grade')),[]);m=statistics.median(ps) if ps else None;p=x.get('price')
  ls.append({'sku':x.get('sku'),'name':x.get('name'),'grade':x.get('grade'),'price':p,'median':m,'gap_pct':round((p/m-1)*100,2) if m and isinstance(p,(int,float)) else None,'market_count':len(ps),'b_median':statistics.median(sales[(x.get('sku'),'B')]) if sales.get((x.get('sku'),'B')) else None})
 cards=[{'name':x.get('name'),'rank':x.get('rank'),'description':(x.get('card') or {}).get('description','')} for x in sorted((x for x in bb if isinstance(x,dict)),key=lambda x:x.get('rank') if isinstance(x.get('rank'),int) else 999999)[:3]]
 return {'settles_per_shop':dict(counts.most_common()),'market_settles':sum(counts.values()),'top15':top,'top3_cards':cards,'our_lines':ls,'sample_from':min(times) if times else None,'sample_to':max(times) if times else None}
def getlogs(path='customers.jsonl'):
 out=[]
 try:
  for line in Path(path).read_text(encoding='utf8').splitlines():
   try:
    x=json.loads(line)
    if isinstance(x,dict):out.append(x)
   except Exception:pass
 except FileNotFoundError:pass
 return out
def real(x):
 return '연결점검' not in json.dumps(x,ensure_ascii=False)
def checkout(x):
 reply=x.get('reply',{});return bool(x.get('checkout_jwt') or (isinstance(reply,dict) and (reply.get('data') or {}).get('checkout_jwt')) or x.get('checkout'))
def own(r,kit):
 d=r.get('data') or {};return norm(d.get('shop_url') or d.get('shop')) in (norm(kit.shop_url),norm(kit.name))
def metrics(l,logs,now,kit):
 settles=[r for r in rows(l) if isinstance(r,dict) and r.get('kind')=='settle' and r.get('round',4)==4 and now-21600<=stamp(r)<=now+10];recent=[x for x in logs if now-21600<=stamp(x)<=now+10 and real(x)]
 h=[x for x in recent if stamp(x)>=now-3600];hs=[r for r in settles if stamp(r)>=now-3600];day=now-((now+32400)%86400)
 today=sum(own(r,kit) and stamp(r)>=day for r in rows(l) if isinstance(r,dict) and r.get('kind')=='settle' and r.get('round',4)==4)
 return {'msgs':len(recent),'checkouts':sum(checkout(x) for x in recent),'settled':sum(own(r,kit) for r in settles),'market_settled':len(settles),'hour':{'msgs':len(h),'checkouts':sum(checkout(x) for x in h),'settled':sum(own(r,kit) for r in hs),'market_settled':len(hs)},'today':today,'sample_from':min((stamp(r) for r in rows(l) if isinstance(r,dict) and stamp(r)),default=None),'recent_logs':[{'ts':stamp(x),'text':str(x.get('text',''))[:140],'checkout':checkout(x)} for x in h]}
def card(url,kit,fixtures=None):
 if fixtures is not None:return fixtures.get(url,{})
 u=urlsplit(url)
 if u.scheme!='https' or not (u.hostname=='market.ourolabs.ai' or u.hostname=='trycloudflare.com' or (u.hostname or '').endswith('.trycloudflare.com')):return {'error':'host not permitted','host':u.hostname}
 try:
  r=httpx.get(url,timeout=8,follow_redirects=False);return r.json() if r.status_code==200 else {'error':'HTTP '+str(r.status_code)}
 except Exception as e:return {'error':str(e)[:100]}
def run(a,kit):
 try:
  mode=a.get('mode');now=a.get('now',time.time())
  if mode=='scan':
   if kit.testing:l=a['ledger_fixture'];s=a['shops_fixture'];b=a['board_fixture'];c=a['catalog_fixture']
   else:l=req(kit,'/api/ledger?after=-500');s=req(kit,'/api/shops');b=req(kit,'/api/board');c=json.loads(Path('public/catalog.json').read_text(encoding='utf8'))
   return {'ok':True,**sc(l,s,b,c)}
  if mode=='metrics':
   l=a['ledger_fixture'] if kit.testing else req(kit,'/api/ledger?after=-500');logs=a.get('logs_fixture',[]) if kit.testing else getlogs()
   return {'ok':True,**metrics(l,logs,now,kit)}
  if mode=='inventory':
   b=a['inventory_fixture'] if kit.testing else req(kit,'/api/inventory',True);groups=defaultdict(list);skus=a.get('skus',[])
   for u in b.get('units',[]):
    if not skus or u.get('sku') in skus:groups[(u['sku'],u['grade'])].append(u)
   lots=[]
   for (sku,g),us in groups.items():
    es=[u['expires_at'] for u in us if u.get('expires_at')];row={'sku':sku,'grade':g,'qty':len(us),'min_cost':min(u['cost'] for u in us),'max_cost':max(u['cost'] for u in us),'first_expiry':min(es) if es else None}
    if skus:row['units']=[{k:u.get(k) for k in ('unit','cost','supplied_at','expires_at')} for u in us]
    lots.append(row)
   return {'ok':True,**{k:b.get(k) for k in ('round','balance','wallet','tokrw','storage_due_with_next_lot','restock','next_dislike_fee')},'unit_count':len(b.get('units',[])),'sku_count':len({u['sku'] for u in b.get('units',[])}),'lots':lots}
  if mode=='discovery':
   ss=items(a['shops_fixture'] if kit.testing else req(kit,'/api/shops'),'shops');me=next((x for x in ss if norm(x.get('url'))==norm(kit.shop_url)),None)
   return {'ok':True,'listed':bool(me),'own':me,'coverage':[]}
  if mode=='review':
   if kit.testing:l=a['ledger_fixture'];ss=a['shops_fixture'];aa=a['agents_fixture'];ff=a['forum_fixture'];cat=a['catalog_fixture'];cf=a.get('cards_fixture',{})
   else:l=req(kit,'/api/ledger?after=-500');ss=req(kit,'/api/shops');aa=req(kit,'/api/agents');ff=req(kit,'/api/forum?role=shop');cat=json.loads(Path('public/catalog.json').read_text(encoding='utf8'));cf=None
   recent=[r for r in rows(l) if isinstance(r,dict) and r.get('kind')=='settle' and r.get('round',4)==4 and now-7200<=stamp(r)<=now+10];summary=sc(recent,ss,{},cat);shoplist=items(ss,'shops');agents=items(aa,'agents');forum=items(ff,'posts');counts=Counter(x.get('author') for x in forum if isinstance(x,dict) and now-3600<=stamp(x)<=now+10 and x.get('role')=='shop');w=[]
   names=list(summary['settles_per_shop'])[:3]+[kit.name]
   for name in names:
    shop=next((x for x in shoplist if x.get('name')==name),{});agent=next((x for x in agents if x.get('name')==name),{});cu=agent.get('card');c=card(cu,kit,cf) if cu else {};stock=shop.get('stock') or {};w.append({'name':name,'description':str(c.get('description',''))[:40],'card':cu,'card_error':c.get('error'),'units':sum(v for v in stock.values() if isinstance(v,(int,float))),'lines_sku':len(stock),'settles':summary['settles_per_shop'].get(name,0),'forum_posts_1h':counts[name]})
   return {'ok':True,'winners':w,'market_2h':len(recent),'our_price_gaps':summary['our_lines'],'sample_from':summary['sample_from'],'forum_sample_from':min((stamp(x) for x in forum if isinstance(x,dict) and stamp(x)),default=None)}
  if mode=='a2a':
   if kit.testing:agents=a['agents_fixture'];fixture=a.get('response_fixture',{});led=a['ledger_fixture'];shops=a['shops_fixture']
   else:agents=req(kit,'/api/agents');led=req(kit,'/api/ledger?after=-500');shops=req(kit,'/api/shops');fixture=None
   recent=[r for r in rows(led) if isinstance(r,dict) and r.get('kind')=='settle' and r.get('round',4)==4 and now-7200<=stamp(r)<=now+10];w=list(sc(recent,shops,{},{}).get('settles_per_shop',{}));name=a.get('shop')
   if not w or name!=w[0] or name==kit.name:raise ValueError('only first winner may be asked')
   agent=next((x for x in items(agents,'agents') if x.get('name')==name and 'shop' in x.get('roles',[])),None)
   if not agent or not agent.get('card'):raise ValueError('shop card missing')
   c=card(agent['card'],kit,a.get('cards_fixture',{}) if kit.testing else None);url=c.get('url');u=urlsplit(str(url or ''));cu=urlsplit(agent['card'])
   if u.scheme!='https' or u.hostname!=cu.hostname:raise ValueError('card endpoint host mismatch')
   msg={'jsonrpc':'2.0','id':str(uuid.uuid4()),'method':'message/send','params':{'message':{'role':'user','messageId':str(uuid.uuid4()),'parts':[{'kind':'text','text':'안녕하세요, Hermes Shop입니다. 지금 어떤 상품을 얼마에 판매하시나요?'}],'metadata':{'from':'Hermes Shop'}}}}
   if kit.testing:response=fixture;status=200
   else:
    r=httpx.post(url,json=msg,timeout=30,follow_redirects=False);status=r.status_code
    try:response=r.json()
    except Exception:response={'text':r.text[:1000]}
   return {'ok':status==200,'status':status,'shop':name,'response':response,'error':None if status==200 else 'peer HTTP '+str(status)}
  path=a.get('path');method=str(a.get('method','GET')).upper()
  if method not in ('GET','POST','PUT','PATCH','DELETE'):raise ValueError('invalid method')
  status,b=request(kit,path,bool(a.get('auth',False)),method,a.get('body'))
  return {'ok':200<=status<300,'status':status,'body':b,**({} if 200<=status<300 else {'error':'HTTP '+str(status)})}
 except Exception as e:return {'ok':False,'error':str(e)[:300]}
