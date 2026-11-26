import base64,json,time,uuid
from pathlib import Path
def test(run,kit):
 p=Path('tmp/test');p.mkdir(parents=True,exist_ok=True)
 names=[('y','그릭요거트','C',4990),('tea','둥굴레차','B',3251),('kim','총각김치 단단한','B',9119),('nam','취나물','B',2990),('nam','취나물','C',2590)]
 items=[];units=[]
 for i,(sku,name,grade,price) in enumerate(names):
  u='unit-'+str(i);items.append({'sku':sku,'name':name,'grade':grade,'price':price,'stock':1,'units':[u],'warranty_hours':0});units.append({'unit':u,'sku':sku,'grade':grade,'cost':1000,'supplied_at':100,'expires_at':time.time()+10000})
 cp=p/'handler_catalog.json';cp.write_text(json.dumps({'items':items},ensure_ascii=False),encoding='utf8')
 def call(text):
  suffix=uuid.uuid4().hex
  return run({'text':text,'catalog_path':str(cp),'holds_path':str(p/('h'+suffix+'.json')),'customers_path':str(p/('c'+suffix+'.jsonl')),'reservations_path':str(p/'reservations_missing.jsonl'),'inventory_fixture':{'units':units}},kit)
 r=call('냉장고와 소포장 우유 있나요? 결제서 주세요');assert not r.get('data',{}).get('checkouts') and '냉장고' in r['reply'] and '우유' in r['reply'],r
 r=call('단단한 두부와 차 있으면 결제서 주세요');assert [x['sku'] for x in r['data']['checkouts']]==['tea'] and '두부' in r['reply'],r
 r=call('요거트랑 샴푸·치약, 있으면 결제서 주세요');assert [x['sku'] for x in r['data']['checkouts']]==['y'] and '샴푸' in r['reply'] and '치약' in r['reply'],r
 r=call('취나물 A등급 구매할게요');assert not r['data']['checkouts'] and 'B' in r['reply'] and 'C' in r['reply'],r
 r=call('둥굴레차 구매');c=r['data']['checkouts'];assert len(c)==1,r
 jwt=c[0]['checkout_jwt'];parts=jwt.split('.');assert len(parts)==3 and all(parts)
 decode=lambda s:json.loads(base64.urlsafe_b64decode(s+'='*((-len(s))%4)))
 assert decode(parts[0])=={'alg':'EIP191','typ':'JWT'}
 payload=decode(parts[1]);assert all(payload.get(k) for k in ('id','shop','shop_url','item','price','task','currency','iat','unit')),payload
 assert payload['unit']=='unit-1' and payload['item']=='tea'
 assert kit.sign_jwt(payload,'shop')==jwt
