from pathlib import Path
import json,time,uuid

def test(run,kit):
 p=Path('tools/.deprecated/a2a_handler@29/test.py')
 if not p.exists():p=Path('tools/a2a_handler/test.py')
 ns={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns);ns['test'](run,kit)
 tag=uuid.uuid4().hex;root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True)
 def path(s):return str(root/(tag+s))
 uid=tag+'u';sku='G0746760c'
 Path(path('cat')).write_text(json.dumps({'items':[{'sku':sku,'name':'동서 둥굴레차 50T','grade':'B','price':1000,'stock':1,'units':[uid],'warranty_hours':0}]},ensure_ascii=False))
 u={'unit':uid,'sku':sku,'grade':'B','cost':100,'expires_at':time.time()+3600,'cert':{'cert':{'grade':None}}}
 a={'catalog_path':path('cat'),'holds_path':path('hold'),'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':path('wanted'),'replies_path':path('replies'),'loss_path':path('loss'),'inventory_fixture':{'units':[u]},'ledger_fixture':[{'kind':'settle','data':{'sku':sku,'grade':'B','amount':1100}}],'text':'둥굴레차 B등급을 인증서에도 같은 등급이 명시된 결제서로 부탁합니다.'}
 r=run(a,kit);assert not (r.get('data') or {}).get('checkouts'),r;assert '인증서' in r['reply'] and '등급' in r['reply'],r
