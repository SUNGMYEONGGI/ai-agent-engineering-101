import json,time,statistics
from collections import defaultdict,Counter
from pathlib import Path
from urllib.parse import urlsplit
import httpx

def norm(v):return str(v or '').rstrip('/').lower()
def get(kit,path,auth=False,method='GET',body=None):
 if not path.startswith('/api/') or path.startswith('//'):raise ValueError('invalid API path')
 r=httpx.request(method,kit.market.rstrip('/')+path,headers={'Authorization':'Bearer '+kit.token('shop')} if auth else {},json=body,timeout=12,follow_redirects=False)
 try:x=r.json()
 except Exception:x={'text':r.text[:300]}
 return r.status_code,x
def rows(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):return x.get('entries',x.get('ledger',[]))
 return []
def scan(ledger,shops,board,catalog):
 shops=shops.get('shops',[]) if isinstance(shops,dict) else shops
 board=board.get('shops',[]) if isinstance(board,dict) else board
 if not isinstance(shops,list) or not isinstance(board,list) or not isinstance(ledger,(list,dict)):raise ValueError('scan response format')
 byurl={norm(x.get('url')):x.get('name') for x in shops if isinstance(x,dict) and x.get('url')}
 counts=Counter();sales=defaultdict(list);names={};timestamps=[]
 for row in rows(ledger):
  if not isinstance(row,dict) or row.get('kind')!='settle' or row.get('round',4)!=4:continue
  d=row.get('data') or {};url=norm(d.get('shop_url') or d.get('shop'));counts[byurl.get(url) or d.get('shop') or '?']+=1
  sku=d.get('sku') or (d.get('item') if isinstance(d.get('item'),str) else (d.get('item') or {}).get('sku'));grade=d.get('grade');p=d.get('amount',d.get('price'))
  if sku and grade and isinstance(p,(int,float)) and p>0:sales[(sku,grade)].append(p);names[sku]=d.get('name','') or names.get(sku,'')
  if isinstance(row.get('ts'),(int,float)):timestamps.append(row['ts'])
 top=[{'sku':sku,'grade':g,'name':names.get(sku,''),'count':len(ps),'median':statistics.median(ps)} for (sku,g),ps in sorted(sales.items(),key=lambda x:(-len(x[1]),x[0]))[:15]]
 lines=[]
 for x in catalog.get('items',[]):
  ps=sales.get((x.get('sku'),x.get('grade')),[]);med=statistics.median(ps) if ps else None
  lines.append({'sku':x.get('sku'),'name':x.get('name'),'grade':x.get('grade'),'price':x.get('price'),'median':med,'gap_pct':round((x['price']/med-1)*100,2) if med and isinstance(x.get('price'),(int,float)) else None,'market_count':len(ps),'b_median':statistics.median(sales[(x.get('sku'),'B')]) if sales.get((x.get('sku'),'B')) else None})
 cards=[]
 for x in sorted((x for x in board if isinstance(x,dict)),key=lambda x:x.get('rank') if isinstance(x.get('rank'),int) else 999999)[:3]:
  c=x.get('card') or {};cards.append({'name':x.get('name'),'rank':x.get('rank'),'description':c.get('description','')})
 return {'settles_per_shop':dict(counts.most_common()),'market_settles':sum(counts.values()),'top15':top,'top3_cards':cards,'our_lines':lines,'sample_from':min(timestamps) if timestamps else None,'sample_to':max(timestamps) if timestamps else None}
def run(a,kit):
 try:
  mode=a.get('mode')
  if mode=='scan':
   if kit.testing:ledger=a['ledger_fixture'];shops=a['shops_fixture'];board=a['board_fixture'];catalog=a['catalog_fixture']
   else:
    vals=[]
    for path in ('/api/ledger?after=-500','/api/shops','/api/board'):
     status,b=get(kit,path)
     if status!=200:raise ValueError(path+' HTTP '+str(status))
     vals.append(b)
    ledger,shops,board=vals;catalog=json.loads(Path('public/catalog.json').read_text(encoding='utf8'))
   return {'ok':True,**scan(ledger,shops,board,catalog)}
  if mode=='inventory':
   s,b=get(kit,'/api/inventory',True)
   if s!=200:raise ValueError('inventory HTTP '+str(s))
   skus=a.get('skus',[]);groups=defaultdict(list)
   for u in b['units']:
    if not skus or u.get('sku') in skus:groups[(u['sku'],u['grade'])].append(u)
   lots=[]
   for (sku,grade),us in groups.items():
    es=[u['expires_at'] for u in us if u.get('expires_at')];row={'sku':sku,'grade':grade,'qty':len(us),'min_cost':min(u['cost'] for u in us),'max_cost':max(u['cost'] for u in us),'first_expiry':min(es) if es else None}
    if skus:row['units']=[{k:u.get(k) for k in ('unit','cost','supplied_at','expires_at')} for u in us]
    lots.append(row)
   return {'ok':True,**{k:b.get(k) for k in ('round','balance','wallet','tokrw','storage_due_with_next_lot','restock','next_dislike_fee')},'unit_count':len(b['units']),'sku_count':len({u['sku'] for u in b['units']}),'lots':lots}
  if mode=='metrics':
   now=a.get('now',time.time());s,l=get(kit,'/api/ledger?after=-500')
   if s!=200:raise ValueError('ledger HTTP '+str(s))
   logs=[]
   try:
    for line in Path('customers.jsonl').read_text(encoding='utf8').splitlines():
     try:logs.append(json.loads(line))
     except Exception:pass
   except FileNotFoundError:pass
   def ts(x):return x.get('ts',x.get('at',0))
   recent=[x for x in logs if now-21600<=ts(x)<=now+10]
   settles=[r for r in rows(l) if r.get('kind')=='settle' and now-21600<=r.get('ts',0)<=now+10]
   own=[r for r in settles if norm((r.get('data') or {}).get('shop'))==norm(kit.shop_url)]
   def check(x):
    reply=x.get('reply',{});return bool(x.get('checkout_jwt') or (isinstance(reply,dict) and (reply.get('data') or {}).get('checkout_jwt')) or x.get('checkout'))
   return {'ok':True,'msgs':len(recent),'checkouts':sum(check(x) for x in recent),'settled':len(own),'market_settled':len(settles),'hour':{'msgs':sum(ts(x)>=now-3600 for x in recent),'checkouts':sum(check(x) and ts(x)>=now-3600 for x in recent),'settled':sum(r['ts']>=now-3600 for r in own)},'sample_from':min((r.get('ts',now) for r in rows(l)),default=None)}
  if mode=='discovery':
   s,b=get(kit,'/api/shops')
   if s!=200:raise ValueError('shops HTTP '+str(s))
   shops=b.get('shops',[]);own=next((x for x in shops if norm(x.get('url'))==norm(kit.shop_url)),None)
   return {'ok':True,'listed':bool(own),'own':own,'coverage':[{'sku':sku,'shops':sum(bool((x.get('stock') or {}).get(sku)) for x in shops)} for sku in a.get('skus',[])]}
  path=a.get('path','/api/board');method=a.get('method','GET').upper()
  if method not in ('GET','POST'):raise ValueError('unsupported method')
  if a.get('url'):
   u=urlsplit(a['url']);base=urlsplit(kit.market)
   if (u.scheme,u.netloc)!=(base.scheme,base.netloc):raise ValueError('external URL forbidden')
   path=u.path+('?' + u.query if u.query else '')
  s,b=get(kit,path,a.get('auth')=='shop',method,a.get('body'));return {'ok':True,'status':s,'body':b}
 except Exception as e:return {'ok':False,'error':str(e)}
