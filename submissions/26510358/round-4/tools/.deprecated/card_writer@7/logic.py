import json,statistics,time
from pathlib import Path
from collections import defaultdict
import httpx
CATS=[('side','반찬·김치',['김치','반찬','고등어']),('protein','계란·두부',['계란','두부','요거트','우유']),('vegetable','채소',['채소','나물','시금치','콩나물','고구마','사과']),('staple','쌀·차·간식',[])]
SHORT=[('계란','계란 20구'),('둥굴레차','둥굴레차'),('총각김치','총각김치 2kg'),('취나물','취나물'),('시금치','시금치'),('쌈채소','쌈채소'),('두부','두부'),('콩나물','콩나물'),('쌀','쌀 2kg'),('고등어','고등어'),('요거트','요거트'),('생수','생수'),('크래커','크래커'),('허브차','허브차')]
def patharg(a,key,default,testing):
 p=Path(a.get(key,default))
 if testing:
  if p.is_absolute() or '..' in p.parts or p.parts[:2]!=('tmp','test'):raise ValueError('test path must be under tmp/test/')
 elif str(p)!=default:raise ValueError('invalid production path')
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
  cp=patharg(a,'catalog_path','public/catalog.json',kit.testing);out=patharg(a,'card_path','card.json',kit.testing);state=patharg(a,'forum_state_path','forum_publish_state.json',kit.testing)
  items=json.loads(cp.read_text(encoding='utf8'))['items']
  if not isinstance(items,list):raise ValueError('invalid catalog')
  products=[]
  for x in items:
   if isinstance(x,dict) and isinstance(x.get('name'),str) and x.get('name') and x.get('sku') and x.get('grade') and type(x.get('price')) is int and x['price']>0 and type(x.get('stock')) is int and x['stock']>0:products.append({k:x[k] for k in ('sku','name','grade','price','stock','warranty_hours','expires_at') if k in x})
  if not products:raise ValueError('no stocked products')
  if kit.testing:ledger=a['ledger_fixture']
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
  eligible=[x for x in products if sales.get((x['sku'],x['grade'])) and x['price']<=statistics.median(sales[(x['sku'],x['grade'])])]
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
  for (sid,title,words),rr in zip(CATS,groups):
   listing=' · '.join('%s %s등급 %s credits'%(x['name'],x['grade'],x['price']) for x in rr) or '현재 해당 분류 재고 없음'
   skills.append({'id':'shop-'+sid,'name':title,'description':listing+'; 상품을 말씀하시면 재고를 확인해 품목마다 결제서를 드립니다.','tags':[title,'상품 구매'],'examples':['%s 구매하고 싶어요'%rr[0]['name']] if rr else [title+' 재고 있나요?']})
  card={'name':'Hermes Shop','description':desc,'skills':skills,'products':products};out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf8')
  result={'ok':True,'products':len(products),'kinds':len(set(x['sku'] for x in products)),'skills':len(skills),'description':desc}
  try:
   now=float(a.get('now',time.time())) if kit.testing else time.time()
   if kit.testing:inventory=a['inventory_fixture'];forum=a['forum_fixture']
   else:
    headers={'Authorization':'Bearer '+kit.token('shop')}
    ir=httpx.get(kit.market.rstrip('/')+'/api/inventory',headers=headers,timeout=12);ir.raise_for_status();inventory=ir.json()
    fr=httpx.get(kit.market.rstrip('/')+'/api/forum?role=shop&limit=500',timeout=12);fr.raise_for_status();forum=fr.json()
   if not isinstance(inventory,dict) or not isinstance(inventory.get('units'),list) or not isinstance(forum,list):raise ValueError('inventory/forum schema')
   last=0
   if state.exists():last=float(json.loads(state.read_text(encoding='utf8')).get('ts',0))
   for f in forum:
    if isinstance(f,dict) and f.get('role')=='shop' and f.get('round',4)==4 and (str(f.get('author','')).casefold()==kit.name.casefold() or str(f.get('owner','')).casefold()==kit.name.casefold()):last=max(last,float(f.get('ts',0)))
   if now-last<1200:result['forum']='skipped: cooldown';return result
   units={u.get('unit'):u for u in inventory['units'] if isinstance(u,dict)};advert=[]
   for x in sorted(eligible,key=rank):
    original=next((v for v in items if isinstance(v,dict) and v.get('sku')==x['sku'] and v.get('grade')==x['grade'] and v.get('price')==x['price']),{})
    live=[units.get(uid) for uid in original.get('units',[])];live=[u for u in live if u and u.get('sku')==x['sku'] and u.get('grade')==x['grade'] and (u.get('expires_at') is None or u['expires_at']>now)]
    if not live:continue
    med=statistics.median(sales[(x['sku'],x['grade'])]);advert.append('%s %s등급 %s크레딧 (최근 중간가 %s)'%(x['name'],x['grade'],x['price'],format(med,'g')))
    if len(advert)==5:break
   if not advert:result['forum']='skipped: no verified eligible stock';return result
   text='[헤르메스 상점] 실재고 안내\n'+'\n'.join('• '+x for x in advert)+'\n상품명을 말씀하시면 재고와 남은 기한을 확인해 드립니다.'
   state.parent.mkdir(parents=True,exist_ok=True);state.write_text(json.dumps({'ts':now}),encoding='utf8')
   if kit.testing:result['forum']='posted (stub)';result['forum_text']=text
   else:
    p=httpx.post(kit.market.rstrip('/')+'/api/forum',headers=headers,json={'text':text,'refs':[]},timeout=12);p.raise_for_status();result['forum']='posted';result['forum_response']=p.json()
  except Exception as e:result['forum']='skipped: '+str(e)[:180]
  return result
 except Exception as e:return {'ok':False,'error':str(e)}