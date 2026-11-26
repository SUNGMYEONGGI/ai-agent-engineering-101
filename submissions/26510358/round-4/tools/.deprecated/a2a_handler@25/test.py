from pathlib import Path
import json,time,uuid
def test(run,kit):
 ns={};exec(compile(Path('ops/a2a_v16_test.py').read_text(encoding='utf8'),'ops/a2a_v16_test.py','exec'),ns);ns['test'](run,kit)
 p=Path('tmp/test');p.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 def path(x):return str(p/(tag+x))
 now=time.time();items=[];units=[];ledger=[]
 for i,name in enumerate(['국내산 시금치 1kg','콩나물 1kg','백미 쌀 2kg','허브차','한계란 난각번호 1번 계란 무항생제 유정란 20구','생 삼겹살','과자','UCC 하와이 커피 337ml','총각김치 2kg']):
  sku='sku'+str(i);uid=tag+str(i);items.append({'name':name,'sku':sku,'grade':'B','price':1000,'stock':1,'units':[uid],'warranty_hours':0});units.append({'unit':uid,'sku':sku,'grade':'B','cost':100,'expires_at':now+3600});ledger.append({'kind':'settle','data':{'sku':sku,'grade':'B','amount':1100}})
 Path(path('cat')).write_text(json.dumps({'items':items},ensure_ascii=False))
 a={'catalog_path':path('cat'),'holds_path':path('hold'),'customers_path':path('customers'),'reservations_path':path('reservations'),'wanted_path':path('wanted'),'replies_path':path('replies'),'loss_path':path('loss'),'inventory_fixture':{'units':units},'ledger_fixture':ledger,'claimed_from':'buyer','text':'안녕하세요. 달걀 30구 한 판만 살 수 있나요? 가능한 재고의 등급, 실제 소비기한, 가격을 확인해 주세요. 조건 맞으면 결제서도 부탁합니다.'}
 r=run(a,kit);assert '달걀 30구' in r['reply'] and '없습니다' in r['reply'] and not (r.get('data') or {}).get('checkouts') and '재고 대안' in r['reply'],r;assert '달걀 30구' in Path(path('wanted')).read_text()
 a['text']='집에서 먹을 김치나 밑반찬하고 봉지 믹스커피를 찾습니다.';r=run(a,kit);assert '믹스커피' in r['reply'] and '없습니다' in r['reply'] and all('UCC' not in x['name'] for x in (r.get('data') or {}).get('checkouts',[])),r
 a['text']='집 반찬용 돼지고기나 닭고기, 계란하고 아이들 간식 과자 재고 있나요?';r=run(a,kit);assert '닭고기' in r['reply'] and '없습니다' in r['reply'],r
 a['text']='두부와 찌개용 신선 채소, 소량 과일을 찾습니다.';r=run(a,kit);assert '두부' in r['reply'] and '과일' in r['reply'],r
 Path(path('hold')).write_text('{}');a['text']='C등급 시금치는 사지 않을게요. 보유 중인 B등급 제철 채소가 실제 배정 가능한지, 품목·수량·남은 소비기한·가격을 알려주세요. 조건이 괜찮으면 그 품목과 가격이 정확히 일치하는 서명 결제서를 부탁드립니다.';r=run(a,kit);assert (r.get('data') or {}).get('checkouts') and all(x['grade']=='B' for x in r['data']['checkouts']),r
 Path(path('hold')).write_text('{}');a['text']='포럼에 올리신 난각번호 1번 무항생제 유정란 20구 B등급 7,695원, 아직 실제 재고 있고 결제 가능한가요? 소비기한이 언제까지인지도 알려주세요. 확인되면 가게 지갑에서 서명한 결제 안내 부탁해요.';r=run(a,kit);assert (r.get('data') or {}).get('checkouts') and all('유정란' in x['name'] for x in r['data']['checkouts']),r
 Path(path('hold')).write_text('{}');a['text']='현미 2kg 찾습니다.';r=run(a,kit);assert not (r.get('data') or {}).get('checkouts') and '현미' in r['reply'] and '재고 대안' in r['reply'],r;assert sum(name in r['reply'] for name in ['시금치','콩나물','백미','허브차','계란'])>=3,r