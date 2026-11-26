import json,os,base64

def dec(p):
 p+='='*(-len(p)%4)
 return json.loads(base64.urlsafe_b64decode(p).decode('utf8'))

def test(run,kit):
 d='tmp/test/a2a9'; os.makedirs(d,exist_ok=True)
 cp=d+'/catalog.json'; rp=d+'/res.jsonl'; lp=d+'/cust.jsonl'; hp=d+'/holds.json'
 for p in (rp,lp,hp):
  if os.path.exists(p):os.remove(p)
 cat={'items':[{'sku':'G159be1f8','name':'[반찬천국] 취나물','category':'식품>반찬','grade':'C','price':2190,'stock':1,'units':['u-ff3749e7ead9'],'warranty_hours':0},{'sku':'G35745411','name':'국내산 시금치 1kg','category':'식품>야채','grade':'B','price':6690,'stock':1,'units':['u-92edcd1927b8'],'warranty_hours':0},{'sku':'G0026722f','name':'무타공 클립형 키친타올 걸이','category':'주방용품','grade':'A','price':4500,'stock':1,'units':['u-0d8bbeb6619e'],'warranty_hours':0}]}
 with open(cp,'w',encoding='utf8') as f:json.dump(cat,f,ensure_ascii=False)
 inv=[{'unit':'u-ff3749e7ead9','sku':'G159be1f8','grade':'C','cost':1479,'expires_at':1795712330,'supplied_at':1},{'unit':'u-92edcd1927b8','sku':'G35745411','grade':'B','cost':6038,'expires_at':1795723285,'supplied_at':1},{'unit':'u-0d8bbeb6619e','sku':'G0026722f','grade':'A','cost':3157,'expires_at':None,'supplied_at':1}]
 base={'catalog_path':cp,'reservations_path':rp,'customers_path':lp,'holds_path':hp,'_test_inventory':inv}
 r=run(dict(base,text='취나물 A등급 재고가 있습니까?',data={},context_id='c1'),kit)
 assert 'data' not in r or not r['data'].get('checkout_jwt'),r
 assert 'C등급' in r['reply'] and 'A등급은 지금 없습니다' in r['reply'],r
 r=run(dict(base,text='요거트 있나요',data={},context_id='c2'),kit)
 assert '시금치' in r['reply'] and '취나물' in r['reply'] and not r.get('data'),r
 r=run(dict(base,text='시금치 주세요',data={},context_id='c3'),kit)
 jwt=r['data']['checkout_jwt']; h,p,s=jwt.split('.')
 assert dec(h)['alg']=='EIP191' and s
 pl=dec(p)
 for k in ['id','shop','shop_url','item','price','task','currency','iat','unit']:
  assert pl.get(k) not in (None,''),k
 assert pl['unit']=='u-92edcd1927b8' and pl['item']=='G35745411' and pl['claim']=='B' and pl['price']==6690
 r=run(dict(base,text='취나물 사고 싶어요',data={},context_id='c4'),kit)
 assert '팔 수 없습니다' in r['reply'] or r['data']['unit']=='u-ff3749e7ead9' or '판매할 수 없습니다' in r['reply'],r
 r=run(dict(base,text='키친타올 걸이 A급',data={},context_id='c5'),kit)
 assert r['data']['unit']=='u-0d8bbeb6619e',r
 r=run(dict(base,text='시금치',data={},context_id='c6'),kit)
 assert not r.get('data') or not r['data'].get('checkout_jwt'),r
 with open(lp,encoding='utf8') as f:n=len([x for x in f if x.strip()])
 assert n==6,n
