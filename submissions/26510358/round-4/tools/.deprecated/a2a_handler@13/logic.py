import json,re,statistics,time
from collections import defaultdict
from pathlib import Path
import httpx
_src=Path('ops/a2a_v11.py').read_text(encoding='utf8')
_base={}
exec(compile(_src,'ops/a2a_v11.py','exec'),_base)
_base['NOUNS'].update({'백미':['쌀','백미'],'현미':['현미'],'잡곡':['잡곡'],'가정용 건조기':['건조기'],'의류건조기':['건조기'],'건조기':['건조기'],'신선채소':['신선채소','채소'],'제철 채소':['채소'],'채소':['채소']})
_base['ORDER']=sorted(_base['NOUNS'],key=len,reverse=True)
def run(a,kit):
 try:
  result=_base['run'](a,kit)
  if result.get('ok') is False:return result
  d=a.get('data') if isinstance(a.get('data'),dict) else {}
  is_payment=any(k in d for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')) or re.search(r'환불|파손|보증\s*청구',str(a.get('text','')))
  if not is_payment:
   text=str(a.get('text') or '');requests=_base['wanted'](text);reply=result.get('reply','');checks=result.get('data',{}).get('checkouts',[])
   missing=[]
   for noun,grade in requests:
    if (noun+'은(는) 없습니다' in reply or noun+' '+str(grade)+'등급은 없습니다' in reply or re.search(re.escape(noun)+r'.{0,30}없습니다',reply)):missing.append(noun)
   if not requests and not checks:
    m=re.search(r'([가-힣A-Za-z0-9 ]{2,25}?)(?:\s*(?:재고|있나요|있습니까|구매|판매))',text)
    if m:missing=[m.group(1).strip()]
   wp=_base['checked_path'](a,'wanted_path','wanted.jsonl',kit.testing)
   if missing:
    wp.parent.mkdir(parents=True,exist_ok=True)
    with wp.open('a',encoding='utf8') as f:
     for item in missing:f.write(json.dumps({'ts':int(time.time()),'item':item,'buyer':a.get('claimed_from')},ensure_ascii=False)+'\n')
   if not checks and (missing or not requests):
    if missing and '없습니다' not in reply:reply='요청하신 '+', '.join(missing)+' 재고는 확인되지 않았습니다.'
    try:
     cp=_base['checked_path'](a,'catalog_path','public/catalog.json',kit.testing);items=_base['load'](cp,{}).get('items',[])
     if kit.testing:ledger=a.get('ledger_fixture',[]);inventory=a.get('inventory_fixture',{})
     else:
      lr=httpx.get(kit.market.rstrip('/')+'/api/ledger?after=-500',timeout=8);lr.raise_for_status();ledger=lr.json()
      ir=_base['api'](kit,'/api/inventory');ir.raise_for_status();inventory=ir.json()
     if isinstance(ledger,dict):ledger=ledger.get('entries',ledger.get('ledger',[]))
     sales=defaultdict(list)
     for row in ledger:
      if row.get('kind')!='settle' or row.get('round',4)!=4:continue
      x=row.get('data') or {};v=x.get('amount',x.get('price'))
      if x.get('sku') and x.get('grade') and isinstance(v,(int,float)) and v>0:sales[(x['sku'],x['grade'])].append(v)
     units={u.get('unit'):u for u in inventory.get('units',[])};opts=[];seen=set();now=time.time()
     for x in items:
      key=(x.get('sku'),x.get('grade'));prices=sales.get(key,[])
      if not prices or x.get('price',float('inf'))>statistics.median(prices) or key in seen:continue
      live=[units.get(uid) for uid in x.get('units',[])];live=[u for u in live if u and u.get('sku')==key[0] and u.get('grade')==key[1] and (not _base['tm'](u.get('expires_at')) or _base['tm'](u['expires_at'])>now)]
      if not live:continue
      seen.add(key);opts.append('%s %s등급 %s credits'%(x['name'],x['grade'],x['price']))
      if len(opts)==5:break
     if opts:reply+='\n현재 재고 대안 (최근 동등급 중간가 이하): '+', '.join(opts)+'. 원하시면 소비기한을 확인해 결제서를 드립니다.'
    except Exception:reply+='\n다른 상품의 재고와 가격을 확인해 드리겠습니다.'
   result['reply']=reply
  try:
   p=_base['checked_path'](a,'replies_path','customer_replies.jsonl',kit.testing);p.parent.mkdir(parents=True,exist_ok=True)
   row={'ts':time.time(),'task_id':a.get('task_id'),'context_id':a.get('context_id'),'claimed_from':a.get('claimed_from'),'text':a.get('text',''),'reply':result.get('reply',''),'checkout':bool((result.get('data') or {}).get('checkouts')),'payment':bool(is_payment)}
   with p.open('a',encoding='utf8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
  except Exception:pass
  return result
 except Exception as e:return {'ok':False,'error':str(e),'state':'input_required','reply':'재고 확인에 문제가 생겼습니다. 잠시 후 다시 문의해 주세요.'}
