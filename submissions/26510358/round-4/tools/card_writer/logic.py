import json
from pathlib import Path

PRIORITY=['계란','둥굴레차','총각김치','시금치','취나물','쌈채소','두부','쌀','고등어','사과','요거트','채소','김치']
CATS=[('side','반찬·김치',['김치','반찬','고등어']),('protein','계란·두부',['계란','두부','요거트','우유']),('vegetable','채소',['채소','나물','시금치','콩나물','고구마','사과']),('staple','쌀·차·간식',[])]
def patharg(args,key,default,testing):
 p=Path(args.get(key,default))
 if testing:
  if p.is_absolute() or '..' in p.parts or p.parts[:2]!=('tmp','test'): raise ValueError('test path must be under tmp/test/')
 elif str(p)!=default: raise ValueError('invalid production path')
 return p
def run(args,kit):
 try:
  cp=patharg(args,'catalog_path','public/catalog.json',kit.testing); out=patharg(args,'card_path','card.json',kit.testing)
  items=json.loads(cp.read_text(encoding='utf8'))['items']
  if not isinstance(items,list): raise ValueError('invalid catalog')
  products=[]
  for x in items:
   if isinstance(x,dict) and isinstance(x.get('name'),str) and x.get('name') and x.get('sku') and x.get('grade') and type(x.get('price')) is int and x['price']>0 and type(x.get('stock')) is int and x['stock']>0:
    products.append({k:x[k] for k in ('sku','name','grade','price','stock','warranty_hours','expires_at') if k in x})
  if not products: raise ValueError('no stocked products')
  def rank(x):
   return next((i for i,w in enumerate(PRIORITY) if w in x['name']),len(PRIORITY))
  selected=[]; seen=set()
  for x in sorted(products,key=rank):
   if x['name'] not in seen:
    selected.append(x); seen.add(x['name'])
   if len(selected)==8: break
  desc='[진열 %d종] '%len(set(x['sku'] for x in products))+' · '.join('%s %s등급 %s credits'%(x['name'],x['grade'],x['price']) for x in selected)+' . 여러 가지를 한 번에 말씀하시면 품목마다 결제서를 드립니다'
  groups=[[] for _ in CATS]
  for x in products:
   idx=next((i for i,(_,_,words) in enumerate(CATS[:3]) if any(w in x['name'] for w in words)),3)
   groups[idx].append(x)
  skills=[]
  for (sid,title,words),rows in zip(CATS,groups):
   listing=' · '.join('%s %s등급 %s credits'%(x['name'],x['grade'],x['price']) for x in rows) or '현재 해당 분류 재고 없음'
   skills.append({'id':'shop-'+sid,'name':title,'description':listing+'; 상품을 말씀하시면 재고를 확인해 품목마다 결제서를 드립니다.','tags':[title,'상품 구매'],'examples':['%s 구매하고 싶어요'%rows[0]['name']] if rows else [title+' 재고 있나요?']})
  card={'name':'Hermes Shop','description':desc,'skills':skills,'products':products}
  out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf8')
  return {'ok':True,'products':len(products),'kinds':len(set(x['sku'] for x in products)),'skills':len(skills),'description':desc}
 except Exception as e: return {'ok':False,'error':str(e)}
