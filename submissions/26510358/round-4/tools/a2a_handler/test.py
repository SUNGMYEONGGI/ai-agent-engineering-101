import json,time,uuid
from pathlib import Path
def test(run,kit):
 p=Path('tmp/test');p.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(x):return str(p/(tag+x))
 cat=path('cat');hold=path('hold');loss=path('loss');wp=path('wanted');rp=path('replies')
 now=time.time();day=time.strftime('%Y-%m-%d',time.gmtime(now+32400))
 items=[];units=[];ledger=[]
 for i,(name,sku,cost,price) in enumerate([('한계란 난각번호 1번 계란 무항생제 유정란 20구','egg',9000,7369),('백미 쌀 2kg','rice',100,1000),('둥굴레차','tea',100,1000),('취나물','veg',100,1000),('생수','water',100,1000),('콩나물 1kg','bean',100,1000)]):
  uid=tag+str(i);items.append({'name':name,'sku':sku,'grade':'B','price':price,'stock':1,'units':[uid],'warranty_hours':0});units.append({'sku':sku,'unit':uid,'grade':'B','cost':cost,'expires_at':now+3600});ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':price+100}})
 Path(cat).write_text(json.dumps({'items':items},ensure_ascii=False));args={'catalog_path':cat,'holds_path':hold,'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':wp,'replies_path':rp,'loss_path':loss,'inventory_fixture':{'units':units},'ledger_fixture':ledger,'claimed_from':'buyer'}
 r=run(dict(args,text='계란 20구 B등급 결제서 부탁합니다'),kit);assert not (r.get('data') or {}).get('checkouts'),r
 Path(loss).write_text(json.dumps([{'day':day,'unit':tag+'0','sku':'egg','grade':'B','price':7369,'loss':2000,'active':True}]))
 r=run(dict(args,text='난각번호 1번 계란 무항생제 유정란 20구 B등급 7,369원 상품의 남은 소비기한과 결제서를 부탁합니다.'),kit);assert any(x.get('sku')=='egg' and x.get('price')==7369 for x in (r.get('data') or {}).get('checkouts',[])),r
 Path(hold).unlink(missing_ok=True)
 r=run(dict(args,text='집에서 쓸 제철 채소와 두부 부탁드립니다'),kit);assert any(x.get('sku')=='bean' for x in (r.get('data') or {}).get('checkouts',[])),r;assert '두부' in r['reply'] and '없습니다' in r['reply'],r
 Path(hold).unlink(missing_ok=True)
 r=run(dict(args,text='현미 2kg 재고 있나요?'),kit);assert '현미' in r['reply'] and '대안' in r['reply'],r;assert '현미' in Path(wp).read_text(),r
 Path(hold).unlink(missing_ok=True)
 r=run(dict(args,text='가정용 건조기 재고 있나요?'),kit);assert '건조기' in r['reply'] and '대안' in r['reply'],r
 Path(hold).unlink(missing_ok=True)
 r=run(dict(args,text='계란 B등급 결제서',loss_cap=1000),kit);assert not (r.get('data') or {}).get('checkouts'),r
 assert Path(rp).exists()
