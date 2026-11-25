def test(run,kit):
 import os,json
 os.makedirs('public',exist_ok=True)
 open('public/reservations.jsonl','w').write(json.dumps({'reservation_id':'r1','sku':'s1','unit_price':4500,'unit_id':'u1','expires_at':9999999999})+'\n')
 x=run({'data':{'reservation_id':'r1'},'context_id':'c'},kit)
 assert x['data']['checkout_jwt'] and x['state']=='input_required'
