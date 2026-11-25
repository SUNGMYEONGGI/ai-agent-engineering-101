import json,os,math,re,httpx

def run(args,kit):
 if kit.testing: units=args.get('inventory',[])
 else:
  r=httpx.get(kit.market+'/api/inventory',headers={'Authorization':'Bearer '+kit.token('shop')},timeout=12);r.raise_for_status();units=r.json()['units']
 prices={(x['sku'],x['grade']):x for x in args.get('prices',[])};groups={}
 for u in units:
  key=(u.get('sku'),u.get('grade'))
  if not all(key) or not u.get('unit'):continue
  groups.setdefault(key,[]).append(u)
 out=[]
 for key,us in groups.items():
  us.sort(key=lambda x:(x.get('expires_at') or 9999999999,x.get('supplied_at',0)));spec=prices.get(key,{})
  floor=max(math.ceil((int(u.get('cost',0))+210)/0.99) for u in us);price=max(int(spec.get('price') or us[0].get('list_price') or 0),floor)
  name=us[0].get('name',key[0]);name=re.sub(r'(?:1\+|1\+\+|특|상|A|B|C)\s*등급','',name,flags=re.I).strip()
  out.append({'sku':key[0],'name':name,'category':us[0].get('category',''),'grade':key[1],'price':price,'stock':len(us),'units':[x['unit'] for x in us],'expires_at':min((x['expires_at'] for x in us if x.get('expires_at')),default=None),'warranty_hours':int(spec.get('warranty_hours',0))})
 p=args.get('catalog_path','public/catalog.json');os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
 with open(p,'w',encoding='utf8') as f:json.dump({'items':out},f,ensure_ascii=False)
 return {'count':len(out),'items':out}