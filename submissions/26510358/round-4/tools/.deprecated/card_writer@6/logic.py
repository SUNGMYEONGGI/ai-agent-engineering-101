import json,statistics
from pathlib import Path
from collections import defaultdict
import httpx
CATS=[('side','반찬·김치',['김치','반찬','고등어']),('protein','계란·두부',['계란','두부','요거트','우유']),('vegetable','채소',['채소','나물','시금치','콩나물','고구마','사과']),('staple','쌀·차·간식',[])]
SHORT=[('계란','계란 20구'),('둥굴레차','둥굴레차'),('총각김치','총각김치 2kg'),('취나물','취나물'),('시금치','시금치'),('쌈채소','쌈채소'),('두부','두부'),('콩나물','콩나물'),('쌀','쌀 2kg'),('고등어','고등어'),('요거트','요거트'),('생수','생수'),('크래커','크래커'),('허브차','허브차')]
def patharg(a,key,default,testing):
 p=Path(a.get(key,default))
 if testing:
  if p.is_absolute() or '..' in p.parts or p.parts[:2]!=('tmp','test'): raise ValueError('test path must be under tmp/test/')
 elif str(p)!=default: raise ValueError('invalid production path')
 return p
def short(name):
 for word,n in SHORT:
  if word in name:
   if word=='계란' and '20구' not in name:return '계란'
   if word=='쌀' and '2kg' not in name:return '쌀'
   if word=='총각김치' and '2kg' not in name:return '총각김치'
   return n
 return name[:25]
def run(a,kit):
 try:
  cp=patharg(a,'catalog_path','public/catalog.json',kit.testing);out=patharg(a,'card_path','card.json',kit.testing)
  items=json.loads(cp.read_text(encoding='utf8'))['items']
  if not isinstance(items,list):raise ValueError('invalid catalog')
  products=[]
  for x in items:
   if isinstance(x,dict) and isinstance(x.get('name'),str) and x.get('name') and x.get('sku') and x.get('grade') and type(x.get('price')) is int and x['price']>0 and type(x.get('stock')) is int and x['stock']>0:
    products.append({k:x[k] for k in ('sku','name','grade','price','stock','warranty_hours','expires_at') if k in x})
  if not products:raise ValueError('no stocked products')
  if kit.testing: ledger=a['ledger_fixture']
  else:
   r=httpx.get(kit.market.rstrip('/')+'/api/ledger?after=-500',timeout=12);r.raise_for_status();ledger=r.json()
  if isinstance(ledger,dict):ledger=ledger.get('entries',ledger.get('ledger',[]))
  if not isinstance(ledger,list):raise ValueError('invalid ledger')
  sales=defaultdict(list)
  for row in ledger:
   if not isinstance(row,dict) or row.get('kind')!='settle' or row.get('round',4)!=4:continue
   d=row.get('data') or {};p=d.get('amount',d.get('price'));sku=d.get('sku');grade=d.get('grade')
   if sku and grade and isinstance(p,(int,float)) and not isinstance(p,bool) and p>0:sales[(sku,grade)].append(p)
  def rank(x):return next((i for i,(w,_) in enumerate(SHORT) if w in x['name']),len(SHORT))
  eligible=[]
  for x in products:
   ps=sales.get((x['sku'],x['grade']),[])
   if ps and x['price']<=statistics.median(ps):eligible.append(x)
  chosen=[];seen=set()
  for x in sorted(eligible,key=rank):
   n=short(x['name'])
   if n not in seen:chosen.append(n);seen.add(n)
   if len(chosen)>=8:break
  desc='[진열 %d종] '%len(set(x['sku'] for x in products))
  if chosen:desc+=' · '.join(chosen)+' . 해당 상품은 최근 시장 중간가 이하입니다. '
  else:desc+='등급과 가격을 확인해 드립니다. '
  desc+='여러 가지를 한 번에 말씀하시면 품목마다 결제서를 드립니다. 등급과 남은 기한을 알려드립니다.'
  groups=[[] for _ in CATS]
  for x in products:
   idx=next((i for i,(_,_,words) in enumerate(CATS[:3]) if any(w in x['name'] for w in words)),3);groups[idx].append(x)
  skills=[]
  for (sid,title,words),rows in zip(CATS,groups):
   listing=' · '.join('%s %s등급 %s credits'%(x['name'],x['grade'],x['price']) for x in rows) or '현재 해당 분류 재고 없음'
   skills.append({'id':'shop-'+sid,'name':title,'description':listing+'; 상품을 말씀하시면 재고를 확인해 품목마다 결제서를 드립니다.','tags':[title,'상품 구매'],'examples':['%s 구매하고 싶어요'%rows[0]['name']] if rows else [title+' 재고 있나요?']})
  card={'name':'Hermes Shop','description':desc,'skills':skills,'products':products}
  out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf8')
  return {'ok':True,'products':len(products),'kinds':len(set(x['sku'] for x in products)),'skills':len(skills),'description':desc}
 except Exception as e:return {'ok':False,'error':str(e)}