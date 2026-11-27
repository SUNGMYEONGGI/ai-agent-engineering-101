from pathlib import Path
import json,re,time
p=Path('tools/.deprecated/a2a_handler@32/logic.py')
if not p.exists(): p=Path('tools/a2a_handler/logic.py')
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),globals())
_prior=run

def run(a,kit):
 text=str(a.get('text') or '')
 data=a.get('data') if isinstance(a.get('data'),dict) else {}
 if '취나물' in text and re.search(r'\b(?:100|200)\s*g\b',text,re.I) and not any(k in data for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):
  try:
   cp=b['checked_path'](a,'catalog_path','public/catalog.json',kit.testing)
   cat=json.loads(cp.read_text(encoding='utf8'))
   quantities=set(re.findall(r'\b(100|200)\s*g\b',text,re.I))
   matches=[x for x in cat.get('items',[]) if '취나물' in str(x.get('name','')) and any(re.search(r'(?<!\d)'+re.escape(q)+r'\s*g\b',str(x.get('name','')),re.I) for q in quantities)]
   if not matches:
    msg='요청하신 취나물의 100g 또는 200g 중량을 확인할 수 없어 해당 조건의 결제서는 발급하지 않습니다.'
    alts=_alternatives(a,kit)
    if alts:msg+='\n현재 재고 대안: '+' · '.join(alts)+'\n남은 기한은 문의 시 확인해 드립니다.'
    result={'reply':msg,'state':'input_required'}
    log=b['checked_path'](a,'customers_path','customers.jsonl',kit.testing);log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('a',encoding='utf8') as f:f.write(json.dumps({'ts':time.time(),'text':text,'buyer':a.get('claimed_from'),'reply':result},ensure_ascii=False)+'\n')
    wp=b['checked_path'](a,'wanted_path','wanted.jsonl',kit.testing);wp.parent.mkdir(parents=True,exist_ok=True)
    with wp.open('a',encoding='utf8') as f:f.write(json.dumps({'ts':time.time(),'item':'취나물 100g/200g','buyer':a.get('claimed_from')},ensure_ascii=False)+'\n')
    return result
  except Exception:
   return {'reply':'요청하신 취나물 중량과 재고를 확인하지 못해 결제서를 발급할 수 없습니다.','state':'input_required'}
 return _prior(a,kit)
