from pathlib import Path
import json,time,statistics,httpx
p=Path('tools/.deprecated/a2a_handler@30/logic.py')
if not p.exists(): p=Path('tools/a2a_handler/logic.py')
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),globals())
_old_run=run

def _rows(x,key):
 if isinstance(x,list): return x
 if isinstance(x,dict): return x.get(key,[]) or []
 return []
def _alternatives(a,kit):
 try:
  cat=json.loads(Path(a.get('catalog_path','public/catalog.json')).read_text(encoding='utf8'))
  if kit.testing:
   inv=a.get('inventory_fixture',{}); led=a.get('ledger_fixture',[])
  else:
   h={'Authorization':'Bearer '+kit.token('shop')}
   ri=httpx.get(kit.market.rstrip('/')+'/api/inventory',headers=h,timeout=8);ri.raise_for_status();inv=ri.json()
   rl=httpx.get(kit.market.rstrip('/')+'/api/ledger?after=-500',timeout=8);rl.raise_for_status();led=rl.json()
  units=_rows(inv,'units'); live={u.get('unit'):u for u in units if isinstance(u,dict) and u.get('unit') and (not u.get('expires_at') or float(u['expires_at'])>time.time())}
  try: holds=Path(a.get('holds_path','holds.json')).read_text(encoding='utf8')
  except FileNotFoundError: holds=''
  sales={}
  for e in _rows(led,'entries') or _rows(led,'ledger'):
   if not isinstance(e,dict) or e.get('kind')!='settle':continue
   d=e.get('data') or {};sku=d.get('sku');g=d.get('grade');price=d.get('amount',d.get('price'))
   if sku and g and isinstance(price,(int,float)) and price>0:sales.setdefault((sku,g),[]).append(price)
  found=[];seen=set()
  for item in cat.get('items',[]):
   sku=item.get('sku');g=item.get('grade');price=item.get('price'); ps=sales.get((sku,g),[])
   if not ps or not isinstance(price,(int,float)) or price>statistics.median(ps) or (sku,g) in seen:continue
   avail=[live[uid] for uid in item.get('units',[]) if uid in live and uid not in holds and live[uid].get('sku')==sku and live[uid].get('grade')==g]
   if not avail:continue
   found.append(f"{item.get('name',sku)} {g}등급 {price} credits (시장 중간가 {statistics.median(ps):g})")
   seen.add((sku,g))
   if len(found)>=5:break
  return found
 except Exception:return []

def run(a,kit):
 r=_old_run(a,kit)
 if not isinstance(r,dict) or r.get('defer') or r.get('state')=='rejected':return r
 if any(k in (a.get('data') or {}) for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):return r
 d=r.get('data') or {}
 if any(d.get(k) for k in ('checkouts','checkout','checkout_jwt')):return r
 text=str(r.get('reply') or '')
 if '결제서 180초' in text:return r
 alts=_alternatives(a,kit)
 if alts:r['reply']=text+'\n현재 재고 대안: '+' · '.join(alts)+'\n각 상품의 남은 기한은 문의 시 확인해 드립니다.'
 return r