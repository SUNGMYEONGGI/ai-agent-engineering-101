import json,time,uuid
from pathlib import Path
def test(run,kit):
 p=Path('tmp/test');p.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 cp=p/(tag+'cat');hp=p/(tag+'hold');lg=p/(tag+'customers');rp=p/(tag+'res');wp=p/(tag+'wanted');out=p/(tag+'replies')
 items=[];units=[];ledger=[]
 for i,(name,sku) in enumerate([('백미 쌀 2kg','rice'),('둥굴레차','tea'),('취나물','veg'),('생수','water'),('과자','snack'),('콩나물 1kg','bean')]):
  uid=tag+str(i);items.append({'name':name,'sku':sku,'grade':'B','price':1000,'stock':1,'units':[uid],'warranty_hours':1});units.append({'sku':sku,'unit':uid,'grade':'B','cost':100,'expires_at':time.time()+3600});ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':1200}})
 cp.write_text(json.dumps({'items':items},ensure_ascii=False));args={'catalog_path':str(cp),'holds_path':str(hp),'customers_path':str(lg),'reservations_path':str(rp),'wanted_path':str(wp),'replies_path':str(out),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'claimed_from':'buyer'}
 r=run(dict(args,text='집에서 나물과 국에 쓸 제철 채소나 쌈채소를 찾고 있어요. 지금 실제 판매 가능한 채소가 있으면 품목, 등급, 소비기한, 가격, SKU와 유효한 서명 결제서를 알려주세요. 두부 한 모도 있으면 함께 확인 부탁드려요.'),kit);assert r.get('ok') is not False,r;assert any(x.get('sku')=='bean' for x in r.get('data',{}).get('checkouts',[])),r;assert '두부' in r['reply'] and '없습니다' in r['reply'],r
 hp.unlink(missing_ok=True)
 r=run(dict(args,text='백미 2kg, 신선채소, 둥굴레차'),kit);assert {'rice','tea','bean'}.issubset({x.get('sku') for x in r.get('data',{}).get('checkouts',[])}),r
 hp.unlink(missing_ok=True)
 for text,item in [('가정용 건조기 실제 재고가 있습니까?','건조기'),('현미 2kg 있나요?','현미')]:
  r=run(dict(args,text=text),kit);assert item in r['reply'] and '없습니다' in r['reply'] and '중간가 이하' in r['reply'],r
 assert wp.exists() and '현미' in wp.read_text(encoding='utf8') and '건조기' in wp.read_text(encoding='utf8');assert out.exists()
