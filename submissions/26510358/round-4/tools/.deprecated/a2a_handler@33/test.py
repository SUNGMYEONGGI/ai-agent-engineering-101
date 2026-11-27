from pathlib import Path
import json,time,uuid

def test(run,kit):
 p=Path('tools/.deprecated/a2a_handler@32/test.py')
 if not p.exists():p=Path('tools/a2a_handler/test.py')
 ns={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns);ns['test'](run,kit)
 root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(s):return str(root/(tag+s))
 units=[];items=[];ledger=[]
 for i,n in enumerate(['[반찬천국] 취나물','시금치 1kg','쌀 2kg','콩나물 1kg']):
  sku='G%08x'%(i+1);uid=tag+str(i);items.append({'sku':sku,'name':n,'grade':'B','price':1000,'stock':1,'units':[uid]});units.append({'unit':uid,'sku':sku,'name':n,'grade':'B','cost':100,'expires_at':time.time()+36000});ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':1200}})
 Path(path('cat')).write_text(json.dumps({'items':items},ensure_ascii=False))
 a={'catalog_path':path('cat'),'holds_path':path('holds'),'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':path('wanted'),'replies_path':path('replies'),'loss_path':path('loss'),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'text':'취나물 100g이나 200g 소포장 재고가 있나요? 중량 확인 안 되면 오늘은 안 살게요. 서명 결제서 부탁합니다.'}
 r=run(a,kit);assert '중량' in r['reply'] and '결제서' in r['reply'] and not (r.get('data') or {}).get('checkouts'),r
 assert '시금치' in r['reply'] and '쌀' in r['reply'] and '콩나물' in r['reply'],r
 assert json.loads(Path(path('customers')).read_text())['reply']==r
 assert '취나물' in Path(path('wanted')).read_text()
