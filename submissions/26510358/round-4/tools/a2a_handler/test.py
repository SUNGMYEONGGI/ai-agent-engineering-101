def test(run,kit):
 import os,json,base64
 p='tmp/test/a2a'; os.makedirs(p,exist_ok=True)
 paths={'catalog_path':p+'/catalog.json','reservations_path':p+'/reservations.jsonl','customers_path':p+'/customers.jsonl','holds_path':p+'/holds.json'}
 with open(paths['catalog_path'],'w') as f:json.dump({'items':[{'sku':'T1','name':'맛있는 사과','category':'식품','grade':'A','price':3000,'stock':1,'units':['unit1'],'warranty_hours':0}]},f)
 with open(paths['reservations_path'],'w') as f:f.write('')
 args=dict(paths,text='사과 주세요',context_id='ctx',_test_inventory=[{'unit':'unit1','sku':'T1','grade':'A','cost':1000}]); out=run(args,kit); assert out['state']=='completed'
 jwt=out['data']['checkout_jwt']; payload=json.loads(base64.urlsafe_b64decode(jwt.split('.')[1]+'===')); required=['id','shop','shop_url','item','price','task','currency','iat','unit']; assert all(payload.get(k) is not None and payload.get(k)!='' for k in required); assert payload['unit']=='unit1'; assert jwt==kit.sign_jwt(payload,'shop')
 out=run(dict(paths,text='없는 물건',context_id='z'),kit); assert '사과' in out['reply']; assert len(open(paths['customers_path']).readlines())>=2
