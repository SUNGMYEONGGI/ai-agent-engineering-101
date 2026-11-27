from pathlib import Path
import json,uuid

def test(run,kit):
 p=Path('tools/.deprecated/a2a_handler@33/test.py')
 if not p.exists():p=Path('tools/a2a_handler/test.py')
 ns={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns);ns['test'](run,kit)
 root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(s):return str(root/(tag+s))
 Path(path('cat')).write_text(json.dumps({'items':[{'sku':'G00000001','name':'[반찬천국] 취나물','grade':'B','price':2457,'stock':1,'units':['u']}]},ensure_ascii=False))
 a={'catalog_path':path('cat'),'customers_path':path('customers'),'wanted_path':path('wanted'),'holds_path':path('holds'),'reservations_path':path('reservations'),'replies_path':path('replies'),'inventory_fixture':{'units':[]},'ledger_fixture':[]}
 for text in ['취나물 중량이 몇 g인가요? 실제 포장 중량을 확인해 알려주세요. 확인 전에는 결제하지 않을게요.','취나물 재고 있나요? 실제 등급, 중량, 소비기한과 가격을 알려주세요. 확인한 뒤 살지 정할게요.']:
  r=run(dict(a,text=text),kit);assert '중량' in r['reply'] and ('확인되지' in r['reply'] or '확인하지 못' in r['reply']),r
  assert not (r.get('data') or {}).get('checkouts'),r
 assert '취나물' in Path(path('wanted')).read_text(encoding='utf8')
