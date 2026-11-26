import json
from pathlib import Path
def test(run,kit):
 p=Path('tmp/test/card_catalog.json');p.parent.mkdir(parents=True,exist_ok=True)
 items=[{'sku':'egg','name':'한계란 무항생제 계란 20구','grade':'B','price':9000,'stock':2,'units':['u1'],'warranty_hours':0},{'sku':'tea','name':'동서 둥굴레차 50T 60g','grade':'B','price':2700,'stock':1,'units':['u2'],'warranty_hours':0},{'sku':'rice','name':'2026년 햅쌀 국산 백미 쌀 2kg 소포장','grade':'B','price':4500,'stock':1,'units':['u3'],'warranty_hours':0}]
 p.write_text(json.dumps({'items':items},ensure_ascii=False),encoding='utf8')
 ledger=[{'kind':'settle','round':4,'data':{'sku':'egg','grade':'B','amount':7490}},{'kind':'settle','round':4,'data':{'sku':'tea','grade':'B','amount':2800}},{'kind':'settle','round':4,'data':{'sku':'rice','grade':'B','amount':4600}}]
 args={'catalog_path':str(p),'card_path':'tmp/test/card_out.json','ledger_fixture':ledger};r=run(args,kit);assert r['ok'],r
 card=json.loads(Path(args['card_path']).read_text(encoding='utf8'));desc=card['description']
 assert '둥굴레차 · 쌀 2kg' in desc and '계란' not in desc and '중간가 이하' in desc
 assert '여러 가지를 한 번에 말씀하시면 품목마다 결제서를 드립니다' in desc
 assert len(card['skills'])==4
 for s in card['skills']:assert all(s.get(k) for k in ('id','name','description','tags','examples'))
 assert card['products']==[{k:x[k] for k in ('sku','name','grade','price','stock','warranty_hours') if k in x} for x in items]
 args['ledger_fixture']=[];assert run(args,kit)['ok'];desc=json.loads(Path(args['card_path']).read_text(encoding='utf8'))['description'];assert '중간가 이하' not in desc and '계란' not in desc