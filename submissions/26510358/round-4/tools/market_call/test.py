def test(run,kit):
 sku='G02f9f99c'; unit={'unit':'u-test','sku':sku,'grade':'B','cost':7000,'supplied_at':40000,'expires_at':100000}
 payload={'round':4,'balance':4876216,'restock':{'open':False,'opens_at':51000,'closes_at':51180},'units':[unit,dict(unit,unit='u-test2',cost=7600),dict(unit,unit='u-other',sku='G12345678')]}
 assert all(unit[k] is not None for k in ('unit','sku','grade','cost','supplied_at','expires_at'))
 r=run({'mode':'inventory','skus':[sku],'inventory_fixture':payload},kit)
 assert r['balance']==4876216 and r['sku_count']==2 and len(r['lots'])==1 and r['lots'][0]['max_cost']==7600 and r['lots'][0]['qty']==2 and r['lots'][0]['units'][0]=={k:unit[k] for k in ('unit','cost','supplied_at','expires_at')}
 assert run({'mode':'inventory','inventory_fixture':{'units':[unit]}},kit)['ok'] is False
 qs={'quote':'q-test','total':7010,'expires_in':120,'pay':{'to':'0x'+'1'*40,'wei':'7010000000000000000','data':'0xab'},'units':[unit]}
 r=run({'path':'/api/supply','method':'POST','auth':'shop','body':{'sku':sku,'qty':1},'fixture':qs,'fixture_status':402},kit)
 assert r['status']==402 and r['body']==qs and all(r['body']['pay'][k] for k in ('to','wei','data'))
 assert run({'url':'https://outside.invalid/api/inventory','auth':'shop'},kit)['ok'] is False
 d={'shop':kit.shop_url,'sku':sku,'amount':8390,'grade':'B','unit':'u-test','order':'o-test'}
 r=run({'mode':'metrics','now':50000,'ledger':{'entries':[{'kind':'settle','round':4,'ts':49800,'data':d}]},'customers_fixture':[{'ts':49810,'them':'김치','deal':{'checkout_id':'c1'}}]},kit)
 assert r['hour']=={'msgs':1,'checkouts':1,'settled':1} and r['top_sales'][0]['grade_prices']['B']==8390
 r=run({'mode':'discovery','skus':[sku],'shops_fixture':{'shops':[{'name':'Hermes','url':kit.shop_url,'stock':{sku:2}}]}},kit)
 assert r['listed'] and r['coverage'][0]['own_qty']==2
