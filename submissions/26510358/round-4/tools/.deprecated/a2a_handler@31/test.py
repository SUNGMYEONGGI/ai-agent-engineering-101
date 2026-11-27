from pathlib import Path
import json,time,uuid

def test(run,kit):
 p=Path('tools/.deprecated/a2a_handler@30/test.py')
 if not p.exists():p=Path('tools/a2a_handler/test.py')
 ns={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns);ns['test'](run,kit)
 root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(s):return str(root/(tag+s))
 items=[];units=[];ledger=[]
 for i in range(4):
  sku='G'+format(i+10,'08x');uid=tag+str(i);name=['취나물','백미','시금치','두부'][i]
  items.append({'sku':sku,'name':name,'grade':'B','price':1000+i,'stock':1,'units':[uid],'warranty_hours':0})
  units.append({'unit':uid,'sku':sku,'name':name,'grade':'B','cost':100,'expires_at':time.time()+3600,'cert':{'cert':{'grade':'B'}}})
  ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':1200}})
 Path(path('cat')).write_text(json.dumps({'items':items},ensure_ascii=False))
 a={'catalog_path':path('cat'),'holds_path':path('holds'),'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':path('wanted'),'replies_path':path('replies'),'loss_path':path('loss'),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'text':'가정용 건조기 있나요?'}
 r=run(a,kit);assert not (r.get('data') or {}).get('checkouts'),r
 assert '건조기' in r['reply'] and '현재 재고 대안' in r['reply'],r
 assert all(x in r['reply'] for x in ['취나물','백미','시금치']),r
 a['text']='현미 2kg 있나요?';r=run(a,kit);assert '현미' in r['reply'] and '현재 재고 대안' in r['reply'],r
