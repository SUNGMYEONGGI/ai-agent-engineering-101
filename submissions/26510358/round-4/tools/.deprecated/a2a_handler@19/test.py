from pathlib import Path
import json,time,uuid
def test(run,kit):
 ns={};exec(compile(Path('ops/a2a_v16_test.py').read_text(encoding='utf8'),'ops/a2a_v16_test.py','exec'),ns);ns['test'](run,kit)
 f=run.__globals__['wallet_reply'];assert str(kit.address('shop')) in f('결제서',[{'sku':'x'}],kit);assert f('없음',[],kit)=='없음'
 p=Path('tmp/test');p.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(x):return str(p/(tag+x))
 now=time.time();items=[];units=[];ledger=[]
 for i,name in enumerate(['국내산 시금치 1kg','콩나물 1kg','백미 쌀 2kg','허브차']):
  sku='sku'+str(i);uid=tag+str(i);items.append({'name':name,'sku':sku,'grade':'B','price':1000,'stock':1,'units':[uid],'warranty_hours':0});units.append({'unit':uid,'sku':sku,'grade':'B','cost':100,'expires_at':now+3600});ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':1100}})
 Path(path('cat')).write_text(json.dumps({'items':items},ensure_ascii=False))
 a={'catalog_path':path('cat'),'holds_path':path('hold'),'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':path('wanted'),'replies_path':path('replies'),'loss_path':path('loss'),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'claimed_from':'buyer','text':'김치가 급해서 찾고 있습니다. 사료나 배변패드는 오늘 실제 재고가 확인될 때만 같이 알려주세요.'}
 r=run(a,kit);assert all(s in r['reply'] for s in ['김치','사료','배변패드','시금치','콩나물','백미']),r
 assert all(s in Path(path('wanted')).read_text() for s in ['김치','사료','배변패드'])
 a['text']='안녕하세요. 두부와 찌개용 신선 채소, 둘이 먹을 소량 과일을 찾습니다. 실제 재고 있는 상품의 이름·포장량·가격·등급·남은 소비기한을 알려주세요. 과일은 대용량이나 C등급, 기한 임박은 원하지 않아요.'
 r=run(a,kit);assert '두부' in r['reply'] and '과일' in r['reply'],r;assert '과일' in Path(path('wanted')).read_text(),r;assert '과일' in Path(path('replies')).read_text(),r