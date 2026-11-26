import json
from pathlib import Path
def test(run,kit):
 p=Path('tmp/test/card_catalog.json'); p.parent.mkdir(parents=True,exist_ok=True)
 names=['계란 20구','둥굴레차','총각김치','시금치','취나물','쌈채소','쌀','고등어']
 items=[{'sku':'sku'+str(i),'name':n,'grade':'B','price':1000+i,'stock':2,'units':['u'+str(i)],'warranty_hours':0} for i,n in enumerate(names)]
 p.write_text(json.dumps({'items':items},ensure_ascii=False),encoding='utf8')
 r=run({'catalog_path':str(p),'card_path':'tmp/test/card_out.json'},kit); assert r['ok'],r
 card=json.loads(Path('tmp/test/card_out.json').read_text(encoding='utf8'))
 assert card['description'].startswith('[진열 8종]') and '여러 가지를 한 번에 말씀하시면 품목마다 결제서를 드립니다' in card['description']
 assert sum(x['name'] in card['description'] for x in items)>=5
 for x in items: assert ('%s %s등급 %s credits'%(x['name'],x['grade'],x['price'])) in card['description']
 assert len(card['skills'])==4
 for s in card['skills']: assert all(s.get(k) for k in ('id','name','description','tags','examples'))
 assert card['products']==[{k:x[k] for k in ('sku','name','grade','price','stock','warranty_hours') if k in x} for x in items]
