def test(run,kit):
 import os,json
 os.makedirs('public',exist_ok=True)
 with open('public/catalog.json','w') as f:json.dump({'items':[{'sku':'T1','name':'테스트','grade':'B','price':1000,'stock':1,'warranty_hours':24}]},f)
 with open('public/reservations.jsonl','w') as f:f.write(json.dumps({'reservation_id':'r1','sku':'T1','unit_price':1000,'expires_at':9999999999})+'\n')
 x=run({'text':'구매','data':{'reservation_id':'r1'},'context_id':'c'},kit)
 assert x['state']=='completed' and 'checkout_jwt' in x['data']