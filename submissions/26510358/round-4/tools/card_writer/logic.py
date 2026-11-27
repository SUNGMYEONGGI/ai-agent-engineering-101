import json,time,statistics
from pathlib import Path
from collections import defaultdict
import httpx

def path(a,k,d,test):
 p=Path(a.get(k,d))
 if test:
  if p.is_absolute() or '..' in p.parts or p.parts[:2]!=('tmp','test'): raise ValueError('invalid test path')
 elif str(p)!=d: raise ValueError('invalid path')
 return p

def noun(n):
 for word,label in [('계란','계란 20구' if '20구' in n else '계란'),('둥굴레차','둥굴레차'),('총각김치','총각김치 2kg' if '2kg' in n else '총각김치'),('취나물','취나물'),('시금치','시금치'),('콩나물','콩나물'),('두부','두부'),('우유','우유'),('고등어','고등어'),('가자미','가자미'),('김치','김치'),('커피','커피'),('생수','생수'),('스파게티','스파게티'),('쌀','쌀 2kg' if '2kg' in n else '쌀'),('키친타올','키친타올 걸이')]:
  if word in n:return label
 return n[:12]

def run(a,kit):
 try:
  cp=path(a,'catalog_path','public/catalog.json',kit.testing);out=path(a,'card_path','card.json',kit.testing);state=path(a,'forum_state_path','forum_publish_state.json',kit.testing)
  now=float(a.get('now',time.time())) if kit.testing else time.time();items=json.loads(cp.read_text(encoding='utf8'))['items']
  if kit.testing:ledger=a['ledger_fixture'];inv=a['inventory_fixture'];forum=a['forum_fixture']
  else:
   h={'Authorization':'Bearer '+kit.token('shop')};base=kit.market.rstrip('/')
   r=httpx.get(base+'/api/ledger?after=-500',timeout=10);r.raise_for_status();ledger=r.json()
   r=httpx.get(base+'/api/inventory',headers=h,timeout=10);r.raise_for_status();inv=r.json()
   r=httpx.get(base+'/api/forum?role=shop&limit=100',timeout=10);r.raise_for_status();forum=r.json()
  if isinstance(ledger,dict):ledger=ledger.get('entries',ledger.get('ledger',[]))
  if not isinstance(items,list) or not isinstance(ledger,list) or not isinstance(inv,dict) or not isinstance(inv.get('units'),list) or not isinstance(forum,list):raise ValueError('market schema')
  sales=defaultdict(list)
  for row in ledger:
   if not isinstance(row,dict) or row.get('kind')!='settle' or row.get('round',4)!=4:continue
   d=row.get('data') or {};p=d.get('amount',d.get('price'))
   if d.get('sku') and d.get('grade') and type(p) in (int,float) and p>0:sales[(d['sku'],d['grade'])].append(p)
  live={u.get('unit'):u for u in inv['units'] if isinstance(u,dict) and u.get('unit') and not u.get('sold') and not u.get('held') and str(u.get('status','')).lower() not in ('sold','held','expired','settled')}
  products=[];eligible=[]
  for x in items:
   if not isinstance(x,dict) or not x.get('sku') or not x.get('grade') or not isinstance(x.get('name'),str) or type(x.get('price')) is not int or x['price']<=0:continue
   us=[live[u] for u in x.get('units',[]) if u in live and live[u].get('sku')==x['sku'] and live[u].get('grade')==x['grade'] and (live[u].get('expires_at') is None or live[u]['expires_at']>now)]
   if not us:continue
   p={k:x[k] for k in ('sku','name','grade','price','warranty_hours','expires_at') if k in x};p['stock']=len(us);products.append(p)
   prices=sales.get((x['sku'],x['grade']),[])
   if prices and x['price']<=statistics.median(prices):eligible.append((p,statistics.median(prices)))
  if not products:raise ValueError('no live products')
  eligible.sort(key=lambda z:(noun(z[0]['name']),z[0]['grade']))
  nouns=list(dict.fromkeys(noun(p['name']) for p,m in eligible))[:8]
  desc='[진열 %d종] '%len(set(p['sku'] for p in products))
  desc+=(' · '.join(nouns)+' — 시장 중간가 이하. ' if nouns else '실재고 등급과 가격을 확인해 드립니다. ')
  desc+='여러 품목은 각각 결제서를 드립니다. 등급과 남은 기한을 알려드립니다.'
  groups=[('side','반찬·김치',['김치','반찬','고등어']),('protein','계란·두부',['계란','두부','우유']),('vegetable','채소',['채소','나물','시금치','콩나물']),('staple','쌀·차·간식',[])]
  buckets=[[] for _ in groups]
  for p in products:
   i=next((j for j,g in enumerate(groups[:3]) if any(w in p['name'] for w in g[2])),3);buckets[i].append(p)
  skills=[]
  for (sid,title,_),b in zip(groups,buckets):
   listing=' · '.join('%s %s등급 %s credits'%(p['name'],p['grade'],p['price']) for p in b) or '현재 해당 분류 재고 없음'
   skills.append({'id':'shop-'+sid,'name':title,'description':listing+'; 상품을 말씀하시면 재고를 확인해 품목마다 결제서를 드립니다.','tags':[title,'상품 구매'],'examples':[b[0]['name']+' 구매하고 싶어요'] if b else [title+' 재고 있나요?']})
  card={'name':'Hermes Shop','description':desc,'skills':skills,'products':products};out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf8')
  result={'ok':True,'products':len(products),'kinds':len(set(p['sku'] for p in products)),'skills':len(skills),'description':desc}
  last=float(json.loads(state.read_text(encoding='utf8')).get('ts',0)) if state.exists() else 0
  for f in forum:
   if isinstance(f,dict) and f.get('role')=='shop' and f.get('round',4)==4 and (str(f.get('author','')).casefold()==kit.name.casefold() or str(f.get('owner','')).casefold()==kit.name.casefold()):last=max(last,float(f.get('ts',0)))
  if now-last<600:result['forum']='skipped: cooldown';return result
  if not eligible:result['forum']='skipped: no verified median';return result
  offset=int(now//600)%len(eligible);ordered=eligible[offset:]+eligible[:offset]
  lines=['%s %s등급 %s credits (시장 중간가 %s)'%(p['name'],p['grade'],p['price'],int(m) if int(m)==m else m) for p,m in ordered[:5]]
  text='헤르메스 상점 실재고 안내: '+' · '.join(lines)+' . 등급과 남은 기한을 확인해 드립니다.'
  if not kit.testing:
   r=httpx.post(kit.market.rstrip('/')+'/api/forum',headers=h,json={'text':text},timeout=10);r.raise_for_status();response=r.json()
   if not isinstance(response,dict) or not response.get('post'):raise ValueError('forum post contract')
  state.parent.mkdir(parents=True,exist_ok=True);state.write_text(json.dumps({'ts':now},ensure_ascii=False),encoding='utf8');result.update({'forum':'posted','text':text});return result
 except Exception as e:return {'ok':False,'error':str(e)}
