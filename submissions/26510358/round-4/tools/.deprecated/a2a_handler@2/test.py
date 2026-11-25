import os,json
def test(run,kit):
 os.makedirs('public',exist_ok=True)
 with open('public/reservations.jsonl','w') as f:f.write(json.dumps({'reservation_id':'r1','sku':'x','unit_price':100,'unit':'u1','expires_at':9999999999})+'\n')
 r=run({'reservation_id':'r1'},kit)
 assert r['state']=='completed' and 'checkout_jwt' in r['data']