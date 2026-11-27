from pathlib import Path
import json,time,uuid

def test(run,kit):
 p=Path('tools/.deprecated/a2a_handler@31/test.py')
 if not p.exists():p=Path('tools/a2a_handler/test.py')
 ns={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns);ns['test'](run,kit)
 root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(s):return str(root/(tag+s))
 eggs='Gab7c8b3d';yogurt='G5e1cf31d';items=[];units=[];ledger=[]
 for sku,name,grade in [(eggs,'한계란 난각번호 1번 무항생제 유정란 20구','B'),(yogurt,'후디스 그릭요거트 플레인 400g','C')]:
  uid=tag+sku;items.append({'sku':sku,'name':name,'grade':grade,'price':1000,'stock':1,'units':[uid],'warranty_hours':0})
  units.append({'unit':uid,'sku':sku,'name':name,'grade':grade,'cost':100,'expires_at':time.time()+36000,'cert':{'cert':{'grade':grade}}})
  ledger.append({'kind':'settle','data':{'sku':sku,'grade':grade,'amount':1200}})
 Path(path('cat')).write_text(json.dumps({'items':items},ensure_ascii=False))
 a={'catalog_path':path('cat'),'holds_path':path('holds'),'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':path('wanted'),'replies_path':path('replies'),'loss_path':path('loss'),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'text':'아까는 요거트 C등급뿐이라 안 샀어요. 한계란 20구 B등급 지금 결제 가능한가요? 서명 결제서를 주세요.'}
 r=run(a,kit);assert '요거트' not in r.get('reply',''),r
 d=json.dumps(r.get('data',{}),ensure_ascii=False);assert yogurt not in d,r
 assert '계란' in r.get('reply',''),r
