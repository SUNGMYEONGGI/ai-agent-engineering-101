import httpx,json,time,re,statistics
from urllib.parse import urlsplit,urljoin
from collections import defaultdict,Counter

def num(v): return isinstance(v,(int,float)) and not isinstance(v,bool)
def norm(v): return str(v or '').rstrip('/').removesuffix('/.well-known/agent-card.json').lower()
def bad(msg): return {'ok':False,'error':str(msg)[:450]}
def pick_skus(args):
 skus=args.get('skus',[])
 if not isinstance(skus,list) or len(skus)>15 or any(not isinstance(s,str) for s in skus): raise ValueError('skus: SKU 문자열 최대 15개')
 return skus

def inventory(args,body):
 skus=pick_skus(args)
 if not isinstance(body,dict) or not num(body.get('balance')) or not isinstance(body.get('units'),list): return bad('inventory balance/units 형식 오류')
 groups=defaultdict(list)
 for u in body['units']:
  if not isinstance(u,dict) or not u.get('sku') or not u.get('grade') or not u.get('unit') or not num(u.get('cost')): return bad('inventory unit/sku/grade/cost 형식 오류')
  if not skus or u['sku'] in skus: groups[(u['sku'],u['grade'])].append({k:u.get(k) for k in ('unit','cost','supplied_at','expires_at')})
 allowed=set(list(dict.fromkeys(k[0] for k in groups))[:30]); lots=[]
 for (sku,grade),units in groups.items():
  if sku not in allowed: continue
  expiries=[u['expires_at'] for u in units if num(u['expires_at'])]
  row={'sku':sku,'grade':grade,'qty':len(units),'min_cost':min(u['cost'] for u in units),'max_cost':max(u['cost'] for u in units),'first_expiry':min(expiries) if expiries else None}
  if skus: row['units']=units
  lots.append(row)
 return {**{k:body.get(k) for k in ('round','balance','wallet','tokrw','storage_due_with_next_lot','restock','next_dislike_fee')},'unit_count':len(body['units']),'sku_count':len({u['sku'] for u in body['units']}),'lots':lots}

def discovery(args,kit,body):
 if not isinstance(body,dict) or not isinstance(body.get('shops'),list): return bad('상점 목록 형식 오류')
 shops=[s for s in body['shops'] if isinstance(s,dict) and isinstance(s.get('stock'),dict)]
 here=norm(kit.shop_url); addr=norm(kit.address('shop'))
 by_url=next((s for s in shops if here and norm(s.get('url'))==here),None)
 own=by_url or next((s for s in shops if addr and norm(s.get('pubkey'))==addr),None); stock=own['stock'] if own else {}
 return {'round':body.get('round'),'shop_count':len(shops),'listed':own is not None,'registered_url_matches':bool(by_url),'own':{k:own.get(k) for k in ('name','url','stock')} if own else None,'coverage':[{'sku':s,'shops':sum(bool(x['stock'].get(s)) for x in shops),'own_qty':stock.get(s,0)} for s in pick_skus(args)]}

def metrics(args,kit,ledger):
 now=args.get('now',time.time()); rows=[]
 if not num(now): return bad('now는 Unix 초 숫자')
 if kit.testing: rows=args.get('customers_fixture',[])
 else:
  try:
   with open(args.get('customers_path','customers.jsonl'),encoding='utf8') as f:
    for line in f:
     try:
      x=json.loads(line)
      if isinstance(x,dict) and num(x.get('ts')) and now-21600<=x['ts']<=now+10: rows.append(x)
     except (ValueError,TypeError): pass
  except FileNotFoundError: pass
 rows=[x for x in rows if isinstance(x,dict) and num(x.get('ts')) and now-21600<=x['ts']<=now+10]
 if isinstance(ledger,dict): ledger=ledger.get('entries',ledger.get('ledger'))
 if not isinstance(ledger,list): return bad('원장 entries 형식 오류')
 owned={v for v in (norm(kit.shop_url),norm(kit.address('shop'))) if v}; settled=[]; sales=defaultdict(list); supply={}; stamps=[]; keys=Counter(); market_sales=0
 for x in ledger:
  if not isinstance(x,dict): continue
  d=x.get('data'); t=x.get('ts')
  if num(t): stamps.append(t)
  if x.get('kind')=='supply' and isinstance(d,dict) and isinstance(d.get('sku'),str) and isinstance(d.get('units'),list):
   for u in d['units']:
    if isinstance(u,str): supply[u]=d['sku']
 for x in ledger:
  if not isinstance(x,dict) or x.get('kind')!='settle' or x.get('round',4)!=4: continue
  t=x.get('ts'); d=x.get('data')
  if not num(t) or not now-21600<=t<=now+10 or not isinstance(d,dict): continue
  market_sales+=1; keys.update(d.keys())
  if any(norm(d.get(k)) in owned for k in ('shop_url','shop','shop_wallet')): settled.append(t)
  item=d.get('item'); item=item if isinstance(item,dict) else {'sku':item}; unit=d.get('unit'); unit=unit if isinstance(unit,str) else ''
  sku=next((v for v in (d.get('sku'),item.get('sku'),item.get('id'),supply.get(unit)) if isinstance(v,str) and re.fullmatch(r'G[0-9a-fA-F]{8}',v)),None)
  if not sku: continue
  sales[sku].append((d.get('grade') or item.get('grade'),d.get('amount',d.get('price')),d.get('item_name') or d.get('name') or item.get('name')))
 top=[]
 for sku,items in sorted(sales.items(),key=lambda a:(-len(a[1]),a[0]))[:14]:
  prices=[p for g,p,n in items if num(p) and p>0]; by=defaultdict(list)
  for g,p,n in items:
   if isinstance(g,str) and g in ('A','B','C') and num(p) and p>0: by[g].append(p)
  top.append({'sku':sku,'name':next((n[:80] for g,p,n in reversed(items) if isinstance(n,str) and n),''),'sold':len(items),'median_price':statistics.median(prices) if prices else None,'grade_prices':{g:statistics.median(p) for g,p in sorted(by.items())}})
 def counts(window):
  recent=[x for x in rows if x['ts']>=now-window]; issued=set(); anonymous=0
  for x in recent:
   d=x.get('deal'); token=None
   if isinstance(d,dict):
    if d.get('settled') is True or d.get('status') in ('settled','failed','refunded'): continue
    token=next((d[k] for k in ('checkout_jwt','checkout_id','id') if isinstance(d.get(k),str) and d[k]),None)
   if token: issued.add(token)
   elif d: anonymous+=1
  return {'msgs':len(recent),'checkouts':len(issued)+anonymous,'settled':sum(t>=now-window for t in settled)}
 sample=[{'ts':x['ts'],'them':str(x.get('them',''))[:200],'you':str(x.get('you',''))[:300]} for x in sorted(rows,key=lambda v:v['ts'],reverse=True)[:3]]
 return {**counts(21600),'hour':counts(3600),'ledger_entries':len(ledger),'ledger_span_seconds':round(now-min(stamps)) if stamps else None,'market_settles_6h_in_slice':market_sales,'settle_data_keys':list(keys),'top_sales':top,'recent_messages':sample}

def run(args,kit):
 try:
  base=kit.market.rstrip('/')+'/'
  mode=args.get('mode'); paths={'metrics':'/api/ledger?after=-500','discovery':'/api/shops','inventory':'/api/inventory'}
  if mode is not None and mode not in paths: return bad('알 수 없는 mode')
  url=urljoin(base,paths[mode] if mode else args.get('url') or args.get('path',''))
  p=urlsplit(url); b=urlsplit(base)
  if (p.scheme,p.netloc)!=(b.scheme,b.netloc) or p.fragment: return bad('시장 origin만 허용')
  method='GET' if mode else args.get('method','GET').upper(); auth=('shop' if mode=='inventory' else 'none') if mode else args.get('auth','none')
  if method not in ('GET','POST') or auth not in ('none','shop'): return bad('method/auth 오류')
  headers={'Authorization':'Bearer '+kit.token('shop')} if auth=='shop' else {}
  if kit.testing:
   body=args.get({'metrics':'ledger','discovery':'shops_fixture','inventory':'inventory_fixture'}.get(mode,'fixture'),{})
   status=args.get('fixture_status',200)
  else:
   r=httpx.request(method,url,headers=headers,timeout=24,follow_redirects=False,**({'json':args['body']} if 'body' in args and not mode else {})); status=r.status_code
   try: body=r.json()
   except ValueError: body=r.text[:10000]
  if not (200<=status<300 or (p.path=='/api/supply' and status in (402,429))): return bad(f'HTTP {status}: {str(body)[:380]}')
  if mode=='inventory': return inventory(args,body)
  if mode=='metrics': return metrics(args,kit,body)
  if mode=='discovery': return discovery(args,kit,body)
  return {'status':status,'body':body}
 except Exception as e: return bad(e)
