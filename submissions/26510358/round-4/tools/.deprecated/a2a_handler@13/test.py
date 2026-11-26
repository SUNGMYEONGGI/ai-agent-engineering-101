import json,time,uuid
from pathlib import Path
def test(run,kit):
 p=Path('tmp/test');p.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 cp=p/(tag+'cat');hp=p/(tag+'hold');lg=p/(tag+'customers');rp=p/(tag+'res');wp=p/(tag+'wanted');out=p/(tag+'replies')
 items=[];units=[];ledger=[]
 for i,(name,sku) in enumerate([('백미 쌀 2kg','rice'),('둥굴레차','tea'),('취나물','veg'),('두부','tofu'),('생수','water')]):
  uid=tag+str(i);items.append({'name':name,'sku':sku,'grade':'B','price':1000,'stock':1,'units':[uid],'warranty_hours':1});units.append({'sku':sku,'unit':uid,'grade':'B','cost':100,'expires_at':time.time()+3600});ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':1200}})
 cp.write_text(json.dumps({'items':items},ensure_ascii=False));args={'catalog_path':str(cp),'holds_path':str(hp),'customers_path':str(lg),'reservations_path':str(rp),'wanted_path':str(wp),'replies_path':str(out),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'claimed_from':'buyer'}
 r=run(dict(args,text='백미 2kg, 신선채소, 둥굴레차'),kit);assert len(r.get('data',{}).get('checkouts',[]))==2,r;assert '신선채소' in r['reply'] and '없습니다' in r['reply'],r
 r=run(dict(args,text='가정용 건조기 실제 재고가 있습니까?'),kit);assert '건조기' in r['reply'] and '없습니다' in r['reply'] and '중간가 이하' in r['reply'],r
 r=run(dict(args,text='현미 2kg 있나요?'),kit);assert '현미' in r['reply'] and '없습니다' in r['reply'] and '중간가 이하' in r['reply'],r
 rows=[json.loads(x) for x in wp.read_text().splitlines()];assert {'신선채소','가정용 건조기','현미'}<=set(x['item'] for x in rows),rows
 replies=[json.loads(x) for x in out.read_text().splitlines()];assert len(replies)==3 and replies[-1]['reply']==r['reply'] and replies[0]['checkout'] and not replies[-1]['checkout'],replies
