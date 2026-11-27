import base64,json,time,uuid
from pathlib import Path

def test(run,kit):
 root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True);tag=uuid.uuid4().hex
 names=[('egg','한계란 계란 20구','B',7822),('tea','동서 둥굴레차','B',3051),('tofu','실큰두부 300g','B',2793),('spin','국내산 시금치 1kg','B',5000),('nam','취나물','B',2494),('pasta','아르벨라 스파게티','B',4103)]
 items=[];units=[]
 for i,(sku,name,grade,price) in enumerate(names):
  uid='unit-'+str(i);items.append({'sku':sku,'name':name,'grade':grade,'price':price,'units':[uid],'stock':1,'category':'식품','warranty_hours':0});units.append({'unit':uid,'sku':sku,'grade':grade,'expires_at':time.time()+100000,'kind':'food','cert':{'cert':{'unit':uid,'grade':None},'sig':'market'}})
 cp=root/(tag+'cat');cp.write_text(json.dumps({'items':items},ensure_ascii=False),encoding='utf8')
 messages=[('계란을 사러 왔어요. 혼자 먹으니 20구 정도가 좋습니다. 한계란 난각번호 1번 계란 20구 B등급이 지금 실제 재고인가요? 소비기한이 얼마나 남았는지, 보증 시간과 오늘 가격도 알려주시고, 조건이 맞으면 서명된 결제서 부탁해요. C등급은 사지 않겠습니다.',['egg']),('안내해 주신 둥굴레차는 관심 있는데, 결제서 안쪽 인증서의 grade가 null이라 B등급을 확인할 수 없습니다.',['tea']),('대안 목록의 둥굴레차 B등급 3,051크레딧은 실제 재고가 있는 건가요?',['tea']),('게시판에 올린 실큰두부 300g 한 팩, 지금 실제 재고가 있소? B등급이라고 했는데 가격과 서명 결제서를 보내주시오.',['tofu']),('시금치 B등급 가격과 서명된 결제서 주세요',['spin']),('취나물 B등급 2,508원은 두 식구 먹기 적당한 소량 포장인가요? 남은 소비기한과 보증 여부를 확인해 주세요.',['nam']),('취나물 중량이 몇 g인가요? 실제 포장 중량을 확인해 알려주세요.',['nam']),('집에서 먹을 계란이랑 신선한 나물거리 찾습니다. 계란은 20구 상품의 등급과 정확한 소비기한, 가격을, 취나물은 등급과 수량·가격·소비기한을 알려주세요.',['egg','nam']),('비빔밥 해 먹을 취나물 한 팩하고 찌개 끓일 두부 한 팩 찾습니다.',['nam','tofu']),('아까 문의드린 콩나물 1kg하고 계란 20구, 두부 재고 지금 결제 가능한가요?',['egg','tofu']),('포럼에 올리신 아르벨라 스파게티 실제 재고 있나요?',['pasta']),('대안 목록의 아르벨라 스파게티 B등급 4,103크레딧은 실제 재고가 있는 건가요?',['pasta']),('두부와 시금치 재고 있나요?',['tofu','spin']),('계란 B등급 서명 결제서 주세요',['egg']),('둥굴레차 B등급 3051원 결제서 주세요',['tea'])]
 def call(text,inv=units):
  suffix=uuid.uuid4().hex
  return run({'text':text,'catalog_path':str(cp),'holds_path':str(root/(tag+'h'+suffix)),'customers_path':str(root/(tag+'c'+suffix)),'wanted_path':str(root/(tag+'w'+suffix)),'inventory_fixture':{'units':inv},'decision_fixture':{'answers':[{'choice':'none','probability':0.3}]}},kit)
 for text,expected in messages:
  r=call(text);assert r.get('reply') and r.get('ok') is not False,r
  cs=r.get('data',{}).get('checkouts',[]);assert set(c['sku'] for c in cs)==set(expected),(text,r)
  for c in cs:
   jwt=c['checkout_jwt'];parts=jwt.split('.');assert len(parts)==3 and all(parts)
   dec=lambda s:json.loads(base64.urlsafe_b64decode(s+'='*((-len(s))%4)))
   payload=dec(parts[1]);assert kit.sign_jwt(payload,'shop')==jwt
   assert payload['item']==c['sku'] and payload['unit']==c['unit'] and payload['price']==c['price'] and payload['cert']['cert']['unit']==c['unit']
   assert c['name'] in r['reply'] and c['grade']+'등급' in r['reply'] and str(c['price']) in r['reply']
  assert r['reply'].count('결제서는 Hermes Shop 지갑')==1 and '인증서에는 등급이 없으며' in r['reply']
 r=call('계란 B등급 결제서 주세요',[u for u in units if u['sku']!='egg']);assert not r.get('data',{}).get('checkouts') and '계란' in r['reply'],r
 r=call('계란 B등급 결제서 주세요',[dict(u,sold=True) if u['sku']=='egg' else u for u in units]);assert not r.get('data',{}).get('checkouts'),r
 r=call('계란 B등급 결제서 주세요',[dict(u,expires_at=time.time()-1) if u['sku']=='egg' else u for u in units]);assert not r.get('data',{}).get('checkouts'),r
