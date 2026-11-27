from pathlib import Path
import json,re,time
p=Path('tools/.deprecated/a2a_handler@33/logic.py')
if not p.exists():p=Path('tools/a2a_handler/logic.py')
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),globals())
_prior33=run

def run(a,kit):
 text=str(a.get('text') or '')
 data=a.get('data') if isinstance(a.get('data'),dict) else {}
 if '취나물' in text and re.search(r'중량|무게|몇\s*(?:g|그램)',text,re.I) and not re.search(r'\b(?:100|200)\s*g\b',text,re.I) and not any(k in data for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):
  try:
   cp=b['checked_path'](a,'catalog_path','public/catalog.json',kit.testing)
   cat=json.loads(cp.read_text(encoding='utf8'))
   items=[x for x in cat.get('items',[]) if '취나물' in str(x.get('name','')) and int(x.get('stock',0))>0]
   if not items or any(not re.search(r'(?<!\d)\d+(?:\.\d+)?\s*(?:kg|g|그램|킬로그램)\b',str(x.get('name','')),re.I) for x in items):
    msg='취나물의 실제 포장 중량은 확인되지 않아 알려드릴 수 없으며, 중량 확인 전에는 해당 결제서를 발급하지 않습니다.'
    try:
     alts=_alternatives(a,kit)
     if alts:msg+='\n현재 재고 대안: '+' · '.join(alts)+'\n남은 기한은 문의 시 확인해 드립니다.'
    except Exception:pass
    result={'reply':msg,'state':'input_required'}
    log=b['checked_path'](a,'customers_path','customers.jsonl',kit.testing);log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('a',encoding='utf8') as f:f.write(json.dumps({'ts':time.time(),'text':text,'buyer':a.get('claimed_from'),'reply':result},ensure_ascii=False)+'\n')
    wp=b['checked_path'](a,'wanted_path','wanted.jsonl',kit.testing);wp.parent.mkdir(parents=True,exist_ok=True)
    with wp.open('a',encoding='utf8') as f:f.write(json.dumps({'ts':time.time(),'item':'중량 확인된 취나물','buyer':a.get('claimed_from')},ensure_ascii=False)+'\n')
    return result
   r=_prior33(a,kit)
   weights=sorted(set(re.findall(r'(?<!\d)\d+(?:\.\d+)?\s*(?:kg|g|그램|킬로그램)\b',' '.join(str(x.get('name','')) for x in items),re.I)))
   if weights and isinstance(r,dict) and isinstance(r.get('reply'),str):r['reply']+='\n상품명에 표시된 포장 중량: '+', '.join(weights)+'.'
   return r
  except Exception:
   return {'reply':'취나물 중량과 재고를 확인하지 못해 결제서를 발급할 수 없습니다.','state':'input_required'}
 return _prior33(a,kit)
