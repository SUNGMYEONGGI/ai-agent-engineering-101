import os,json

def test(run,kit):
 sku='Gab7c8b3d'
 # GET /api/shops scoreboard contract: {round, shops:[{name,url,pubkey,reviews,stock}]}
 fixture={'round':4,'shops':[{'name':'Other','url':'https://other.invalid','pubkey':'0x0000000000000000000000000000000000000001','reviews':[],'stock':{sku:3}},{'name':'Hermes','url':str(kit.shop_url).rstrip('/')+'/.well-known/agent-card.json','pubkey':kit.address('shop'),'reviews':[],'stock':{sku:2}}]}
 assert all(set(('name','url','pubkey','reviews','stock'))<=set(s) and all(s[k] is not None for k in ('name','url','pubkey','reviews','stock')) for s in fixture['shops'])
 a=run({'mode':'discovery','shops_fixture':fixture,'skus':[sku]},kit)
 assert a['listed'] and a['registered_url_matches'] and a['coverage']==[{'sku':sku,'shops':2,'own_qty':2}],a
 fixture['shops'].pop()
 assert not run({'mode':'discovery','shops_fixture':fixture},kit)['listed']
 assert run({'mode':'discovery','shops_fixture':[]},kit)['ok'] is False
 assert run({'path':'https://other.invalid/'},kit)['ok'] is False
 os.makedirs('tmp/test',exist_ok=True)
 p='tmp/test/market_customers_summary.jsonl'
 with open(p,'w',encoding='utf8') as f:
  for d in (None,{'id':'co1','unit':'u1'},{'id':'co1','unit':'u1'}): f.write(json.dumps({'ts':99999,'deal':d})+'\n')
 row={'ts':99999,'kind':'settle','round':4,'data':{'shop':kit.shop_url,'sku':sku,'amount':9120,'grade':'A'}}
 out=run({'mode':'metrics','customers_path':p,'now':100000,'ledger':[row]},kit)
 assert (out['msgs'],out['checkouts'],out['settled'])==(3,1,1),out
 assert out['top_sales'][0]['grade_prices']=={'A':9120}
