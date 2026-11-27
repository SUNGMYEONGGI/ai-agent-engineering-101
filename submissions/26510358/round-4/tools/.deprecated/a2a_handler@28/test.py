from pathlib import Path
import json,time,uuid,base64

def test(run,kit):
 ns={};exec(compile(Path('ops/a2a_v16_test.py').read_text(encoding='utf8'),'ops/a2a_v16_test.py','exec'),ns);ns['test'](run,kit)
 p=Path('tmp/test');p.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(x):return str(p/(tag+x))
 now=time.time();items=[];units=[];ledger=[]
 for i,name in enumerate(['국내산 시금치 1kg','콩나물 1kg','백미 쌀 2kg','허브차','한계란 난각번호 1번 계란 무항생제 유정란 20구','생 삼겹살','과자','UCC 하와이 커피 337ml','총각김치 2kg']):
  sku='sku'+str(i);uid=tag+str(i);items.append({'name':name,'sku':sku,'grade':'B','price':1000,'stock':1,'units':[uid],'warranty_hours':0});units.append({'unit':uid,'sku':sku,'grade':'B','cost':100,'expires_at':now+3600});ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':1100}})
 Path(path('cat')).write_text(json.dumps({'items':items},ensure_ascii=False))
 a={'catalog_path':path('cat'),'holds_path':path('hold'),'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':path('wanted'),'replies_path':path('replies'),'loss_path':path('loss'),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'claimed_from':'buyer','text':'달걀 30구 재고와 결제서를 부탁합니다.'}
 r=run(a,kit);assert '달걀 30구' in r['reply'] and '없습니다' in r['reply'] and not (r.get('data') or {}).get('checkouts') and '재고 대안' in r['reply'],r
 a['text']='현미 2kg 찾습니다.';r=run(a,kit);assert not (r.get('data') or {}).get('checkouts') and '현미' in r['reply'] and '재고 대안' in r['reply'],r
 a['text']='상품코드 G4e4eabdb 삼성 일반형 냉장고 RT31CG5624S9 298L를 찾고 있어요.';r=run(a,kit);assert 'G4e4eabdb' in r['reply'] and '재고 대안' in r['reply'],r;assert 'SKU G4e4eabdb' in Path(path('wanted')).read_text()
 a['text']='[으뜸한돈] 국내산 찌개용 돼지고기 1kg (500gX2팩), SKU G97c3d80d를 찾고 있어요. 실제 재고를 확인해 주세요. 조건이 확인되면 서명된 결제서도 부탁드려요.';r=run(a,kit);assert 'G97c3d80d' in r['reply'] and '없습니다' in r['reply'] and not (r.get('data') or {}).get('checkouts') and '재고 대안' in r['reply'],r
 Path(path('hold')).write_text('{}');a['text']='난각번호 1번 무항생제 유정란 20구 B등급 결제서를 부탁합니다.';r=run(a,kit);checks=(r.get('data') or {}).get('checkouts') or [];assert checks,r
 for c in checks:
  tok=c['checkout_jwt'];part=tok.split('.')[1];payload=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)));assert payload['grade']==c['grade']=='B' and payload['unit']==c['unit'] and payload['price']==c['price'],payload