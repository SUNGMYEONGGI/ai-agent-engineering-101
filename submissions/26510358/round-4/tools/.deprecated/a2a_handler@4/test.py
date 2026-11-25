def test(run,kit):
 import os,json,time
 os.makedirs('public',exist_ok=True)
 open('public/catalog.json','w').write(json.dumps({'items':[{'sku':'X','price':100,'stock':1,'grade':'A','warranty_hours':24}]}))
 open('public/reservations.jsonl','w').write(json.dumps({'reservation_id':'r','sku':'X','unit_price':100,'unit':'u','expires_at':time.time()+100})+'\n')
 x=run({'text':'구매','data':{'reservation_id':'r'},'context_id':'c'},kit)
 assert x['state']=='completed' and 'checkout_jwt' in x['data']