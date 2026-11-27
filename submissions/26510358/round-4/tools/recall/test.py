from pathlib import Path
import json,uuid

def test(run,kit):
 p=Path('tmp/test')/uuid.uuid4().hex;p.mkdir(parents=True)
 def write(n,rows):
  f=p/n;f.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf8');return str(f)
 c=write('customers',[{'at':100,'text':'계란','reply':'계란 B','response_data':{'checkouts':[{'checkout_jwt':'stub'}]}},{'at':101,'text':'대안','reply':{'reply':'둥굴레차','data':{'checkout_jwt':'stub'}}},{'at':102,'text':'두부','reply':'없음','response_data':{'checkouts':[]}},{'at':103,'text':'연결점검'},{'at':104,'text':'결제했습니다','data':{'payment_mandate':{}}}]);w=write('wanted',[{'at':102,'item':'두부'}]);r=run({'mode':'customer_summary','since':99,'now':105,'customer_path':c,'wanted_path':w},kit)
 assert r['ok'] and r['inquiries']==3 and r['checkouts']==2 and [x['checkout'] for x in r['messages']]==[True,True,False] and r['wanted']==[('두부',1)],r
 assert 'stub' not in json.dumps(r)
 assert not run({'mode':'read','path':'../harness_check.json'},kit)['ok']
 assert run({'mode':'search','word':''},kit)['count']==0
