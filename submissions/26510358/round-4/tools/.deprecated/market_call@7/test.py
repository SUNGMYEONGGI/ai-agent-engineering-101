import os,json
def test(run,kit):
 os.makedirs('tmp/test',exist_ok=True)
 p='tmp/test/market_customers.jsonl'
 with open(p,'w') as f: f.write(json.dumps({'ts':99999,'deal':None})+'\n'+json.dumps({'ts':99999,'deal':{'unit':'u1'}})+'\n')
 x=run({'mode':'metrics','now':100000,'customers_path':p,'ledger':[{'ts':99999,'kind':'settle','data':{'shop':kit.shop_url}}]},kit)
 assert x['msgs']==2 and x['checkouts']==1 and x['settled']==1
 assert run({'path':'/api/chain'},kit)['status']==200
