import json,os,math,re,httpx

def run(args,kit):
 try:
  p=args.get('catalog_path','public/catalog.json')
  if kit.testing and not os.path.abspath(p).startswith(os.path.abspath('tmp/test')+os.sep):
   raise ValueError('test catalog path must be inside tmp/test')
  try:
   with open(p,encoding='utf8') as f: old=json.load(f)['items']
  except FileNotFoundError: old=[]
  specs={(x['sku'],x['grade']):{k:x[k] for k in ('price','warranty_hours') if k in x} for x in old}
  for x in args.get('prices',[]):
   specs.setdefault((x['sku'],x['grade']),{}).update({k:x[k] for k in ('price','warranty_hours') if k in x})
  if kit.testing: units=args['inventory']
  else:
   r=httpx.get(kit.market.rstrip('/')+'/api/inventory',headers={'Authorization':'Bearer '+kit.token('shop')},timeout=12)
   r.raise_for_status(); units=r.json()['units']
  groups={}
  for u in units:
   key=(u.get('sku'),u.get('grade'))
   if all(key) and u.get('unit'): groups.setdefault(key,[]).append(u)
  out=[]
  for key,us in groups.items():
   us.sort(key=lambda u:(u.get('expires_at') or float('inf'),u.get('supplied_at') or 0)); spec=specs.get(key,{})
   floor=max(math.ceil((int(u['cost'])+210)*100/99) for u in us)
   price=max(int(spec.get('price') or us[0].get('list_price') or 0),floor)
   name=re.sub(r'(?:1\+\+|1\+|특|상|A|B|C)\s*등급','',us[0].get('name') or key[0],flags=re.I).strip().strip('/').strip() or key[0]
   out.append({'sku':key[0],'name':name,'category':us[0].get('category') or '','grade':key[1],'price':price,'stock':len(us),'units':[u['unit'] for u in us],'expires_at':min((u['expires_at'] for u in us if u.get('expires_at')),default=None),'warranty_hours':max(0,int(spec.get('warranty_hours') or 0))})
  os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
  with open(p+'.next','w',encoding='utf8') as f: json.dump({'items':out},f,ensure_ascii=False)
  os.replace(p+'.next',p)
  return {'ok':True,'count':len(out),'items':out}
 except (OSError,ValueError,KeyError,TypeError,httpx.HTTPError) as e:
  return {'ok':False,'error':type(e).__name__+': '+str(e)[:230]}