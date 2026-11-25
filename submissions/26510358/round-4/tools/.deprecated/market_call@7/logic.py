import httpx,json,time,os

def run(args,kit):
 if args.get('mode')=='metrics':
  now=args.get('now',time.time()); rows=[]
  try:
   with open(args.get('customers_path','customers.jsonl'),encoding='utf8') as f:
    for line in f:
     try:
      x=json.loads(line); t=x.get('ts',0)
      if isinstance(t,(int,float)) and t>=now-21600: rows.append(x)
     except (ValueError,TypeError): pass
  except FileNotFoundError: pass
  if kit.testing: ledger=args.get('ledger',[])
  else:
   r=httpx.get(kit.market.rstrip('/')+'/api/ledger?after=-500',timeout=25,follow_redirects=True); r.raise_for_status(); ledger=r.json()
  if isinstance(ledger,dict): ledger=ledger.get('entries',ledger.get('ledger',[]))
  settled=[x for x in ledger if x.get('kind')=='settle' and x.get('ts',0)>=now-21600 and str(x.get('data',{}).get('shop','')).rstrip('/')==kit.shop_url.rstrip('/')]
  return {'msgs':len(rows),'checkouts':sum(bool(x.get('deal')) for x in rows),'settled':len(settled),'ledger_entries':len(ledger),'scope':'last 500 ledger entries; checkout count counts non-null deal records'}
 if kit.testing: return {'status':200,'body':{'ok':True,'test':True}}
 base=args.get('url') or kit.market; path=args.get('path','/'); url=path if path.startswith('http') else base.rstrip('/')+'/'+path.lstrip('/'); headers={}; auth=args.get('auth','none')
 if auth=='shop': headers['Authorization']='Bearer '+kit.token('shop')
 try:
  r=httpx.request(args.get('method','GET').upper(),url,headers=headers,json=args.get('body'),timeout=25,follow_redirects=True)
  try: body=r.json()
  except Exception: body={'text':r.text[:1500]}
  return {'status':r.status_code,'body':body}
 except Exception as e: return {'status':599,'body':{'error':str(e)[:500]}}
