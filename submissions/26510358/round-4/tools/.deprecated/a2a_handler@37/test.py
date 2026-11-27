import json,time,uuid,base64
from pathlib import Path

def test(run,kit):
 root=Path('tmp/test')/uuid.uuid4().hex;root.mkdir(parents=True);now=time.time()
 goods=[('G001','계란 20구','B',7340),('G002','둥굴레차','B',3051),('G003','실큰두부 300g','B',2793),('G004','시금치','B',6000),('G005','취나물','B',2374),('G006','총각김치 2kg','C',5827),('G007','요거트 400g','C',6164),('G008','고등어 800g','C',4950)]
 items=[];units=[]
 for sku,name,g,price in goods:
  uid='u-'+sku;items.append({'sku':sku,'name':name,'grade':g,'price':price,'stock':1,'units':[uid],'warranty_hours':0});units.append({'unit':uid,'sku':sku,'name':name,'grade':g,'kind':'food','expires_at':now+10000,'cert':{'cert':{'unit':uid,'grade':None},'sig':'fixture'}})
 items.append({'sku':'G099','name':'계란 오판','grade':'B','price':1,'units':['u-missing']})
 (root/'catalog.json').write_text(json.dumps({'items':items},ensure_ascii=False))
 messages=[('안녕하세요. 계란이 필요해서요. 한계란 난각번호 1번 계란 무항생제 유정란 20구가 지금 실제 재고인가요?', ['G001']),('계란 B등급 결제서 주세요',['G001']),('둥굴레차 B등급은 대안으로 있나요?',['G002']),('두부 B등급 재고 확인해주세요',['G003']),('시금치 B등급 주세요',['G004']),('취나물 B등급 포장 중량과 결제서 부탁합니다',['G005']),('취나물 B등급 재고가 지금 실제로 구매 가능한가요?',['G005']),('취나물 B등급 2,374원 상품 아직 실제 재고 있나요?',['G005']),('총각김치 2kg C등급 인증서에 C등급과 가격이 명시되고 가게 지갑 서명이 검증되는 결제서를 부탁드립니다.',['G006']),('계란과 시금치 구매합니다',['G001','G004']),('계란과 두부 부탁드려요',['G001','G003']),('아이들 아침용 우유와 요거트가 필요해요. 두유는 찾는 게 아니고',['G007']),('고등어 등급과 가격 결제서 주세요',['G008']),('취나물이나 시금치 실재고 있나요',['G005','G004']),('두부 B등급과 둥굴레차 B등급 결제서 주세요',['G003','G002'])]
 for index,(text,expected) in enumerate(messages):
  a={'text':text,'catalog_path':str(root/'catalog.json'),'holds_path':str(root/('h%d.json'%index)),'customers_path':str(root/'customers.jsonl'),'wanted_path':str(root/'wanted.jsonl'),'inventory_fixture':{'units':units},'decision_fixture':{'answers':[{'choice':'none','probability':1}]}}
  r=run(a,kit);assert r.get('reply') and r.get('data'),r
  out=r['data']['checkouts'];assert set(x['sku'] for x in out)==set(expected),(text,r)
  assert '두유' not in r['reply']
  for c in out:
   assert c['name'] in r['reply'] and c['grade']+'등급' in r['reply'] and str(c['price']) in r['reply']
   token=c['checkout_jwt'];parts=token.split('.');assert len(parts)==3
   payload=json.loads(base64.urlsafe_b64decode(parts[1]+'='*((-len(parts[1]))%4)))
   assert payload['item']==c['sku'] and payload['unit']==c['unit'] and payload['price']==c['price']
   assert token==kit.sign_jwt(payload,'shop') and kit.address('shop')
  assert 'wallets.shop' in r['reply'] and '인증서에는 등급이 없으며' in r['reply']
 a={'text':'계란 B등급 결제서 주세요','catalog_path':str(root/'catalog.json'),'holds_path':str(root/'gone.json'),'customers_path':str(root/'customers.jsonl'),'wanted_path':str(root/'wanted.jsonl'),'inventory_fixture':{'units':units},'fresh_inventory_fixture':{'units':units[1:]},'decision_fixture':{'answers':[{'choice':'G001:B','probability':0.9}]}}
 r=run(a,kit);assert not r['data']['checkouts'] and 'u-missing' not in str(r)
 a['fresh_inventory_fixture']={'units':[dict(units[0],expires_at=now+90)]};r=run(a,kit);assert not r['data']['checkouts']
 a['fresh_inventory_fixture']={'units':[dict(units[0],sold=True)]};r=run(a,kit);assert not r['data']['checkouts']
 a['fresh_inventory_fixture']={'units':units};r=run(a,kit);assert len(r['data']['checkouts'])==1;r2=run(a,kit);assert not r2['data']['checkouts']
 assert (root/'customers.jsonl').exists() and (root/'wanted.jsonl').exists()
