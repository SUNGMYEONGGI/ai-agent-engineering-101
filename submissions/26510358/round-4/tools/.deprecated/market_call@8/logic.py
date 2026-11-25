import httpx,json,time,re,statistics
from urllib.parse import urlsplit,urljoin
from collections import defaultdict,Counter

def number(v):
 return isinstance(v,(int,float)) and not isinstance(v,bool)

def summarize(args,kit,ledger):
 now=args.get('now',time.time()); rows=[]
 try:
  with open(args.get('customers_path','customers.jsonl'),encoding='utf8') as f:
   for line in f:
    try:
     x=json.loads(line); t=x.get('ts',0) if isinstance(x,dict) else 0
     if number(t) and now-21600<=t<=now+10: rows.append(x)
    except (ValueError,TypeError): pass
 except FileNotFoundError: pass
 if isinstance(ledger,dict): ledger=ledger.get('entries',ledger.get('ledger'))
 if not isinstance(ledger,list): return {'ok':False,'error':'원장 entries 형식 오류'}
 settled=[]; sales=defaultdict(list); supply={}; stamps=[]; sale_keys=Counter(); market_sales=0
 own=str(kit.shop_url).rstrip('/')
 for x in ledger:
  if not isinstance(x,dict): continue
  d=x.get('data'); t=x.get('ts'); kind=x.get('kind')
  if number(t): stamps.append(t)
  if not isinstance(d,dict) or kind!='supply': continue
  units=d.get('units'); sku=d.get('sku')
  if isinstance(units,list) and isinstance(sku,str):
   for u in units:
    if isinstance(u,str): supply[u]=sku
 for x in ledger:
  if not isinstance(x,dict) or x.get('kind')!='settle' or x.get('round',4)!=4: continue
  t=x.get('ts'); d=x.get('data')
  if not number(t) or not now-21600<=t<=now+10 or not isinstance(d,dict): continue
  market_sales+=1; sale_keys.update(d.keys())
  if any(isinstance(d.get(k),str) and d[k].rstrip('/')==own for k in ('shop_url','shop')): settled.append(t)
  item=d.get('item'); item=item if isinstance(item,dict) else {'sku':item}; unit=d.get('unit'); unit=unit if isinstance(unit,str) else ''
  sku=next((v for v in (d.get('sku'),item.get('sku'),item.get('id'),supply.get(unit)) if isinstance(v,str) and re.fullmatch(r'G[0-9a-fA-F]{8}',v)),None)
  if not sku: continue
  grade=d.get('grade') or item.get('grade'); price=d.get('price'); name=d.get('item_name') or d.get('name') or item.get('name'); sales[sku].append((grade,price,name))
 top=[]
 for sku,items in sorted(sales.items(),key=lambda a:(-len(a[1]),a[0]))[:14]:
  prices=[p for g,p,n in items if number(p) and p>0]; by=defaultdict(list)
  for g,p,n in items:
   if isinstance(g,str) and g in ('A','B','C') and number(p) and p>0: by[g].append(p)
  name=next((n[:80] for g,p,n in reversed(items) if isinstance(n,str) and n),'')
  top.append({'sku':sku,'name':name,'sold':len(items),'median_price':statistics.median(prices) if prices else None,'grade_prices':{g:statistics.median(p) for g,p in sorted(by.items())}})
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
 sample=[]
 for x in sorted(rows,key=lambda v:v['ts'],reverse=True)[:3]:
  sample.append({'ts':x['ts'],'them':str(x.get('them',''))[:200],'you':str(x.get('you',''))[:300]})
 return {**counts(21600),'hour':counts(3600),'ledger_entries':len(ledger),'ledger_span_seconds':round(now-min(stamps)) if stamps else None,'market_settles_6h_in_slice':market_sales,'settle_data_keys':list(sale_keys),'top_sales':top,'recent_messages':sample}

def run(args,kit):
 try:
  base=kit.market.rstrip('/')+'/'
  if args.get('mode')=='metrics':
   if kit.testing: ledger=args.get('ledger',[])
   else:
    r=httpx.get(urljoin(base,'api/ledger?after=-500'),timeout=25); r.raise_for_status(); ledger=r.json()
   return summarize(args,kit,ledger)
  target=urljoin((args.get('url') or base).rstrip('/')+'/',args.get('path','/')); parsed=urlsplit(target); origin=urlsplit(base)
  if (parsed.scheme,parsed.netloc)!=(origin.scheme,origin.netloc): return {'ok':False,'error':'시장 origin 이외의 URL 거부'}
  auth=args.get('auth','none'); method=args.get('method','GET').upper()
  if auth not in ('shop','none') or method not in ('GET','POST'): return {'ok':False,'error':'method는 GET/POST, auth는 none/shop만 가능'}
  if kit.testing: return {'status':200,'body':{'test':True}}
  headers={'Authorization':'Bearer '+kit.token('shop')} if auth=='shop' else {}
  r=httpx.request(method,target,headers=headers,json=args.get('body'),timeout=25,follow_redirects=False)
  try: body=r.json()
  except ValueError: body={'text':r.text[:1500]}
  result={'status':r.status_code,'body':body}
  if r.is_error and not (parsed.path=='/api/supply' and r.status_code in (402,429)): result.update(ok=False,error='HTTP '+str(r.status_code))
  return result
 except (OSError,ValueError,TypeError,httpx.HTTPError) as e: return {'ok':False,'error':str(e)[:400]}
