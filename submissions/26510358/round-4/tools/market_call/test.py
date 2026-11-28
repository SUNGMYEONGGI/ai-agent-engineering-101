def test(run,kit):
 def v(j,s=200):return {'status':s,'json':j}
 fixture={'GET /api/ledger?after=-5000':v({'entries':[{'seq':1,'kind':'settle','round':4,'ts':1000,'data':{'shop':'Hermes Shop','sku':'G1','grade':'B','amount':3000}}]}),'GET /api/ledger?after=1':v({'entries':[]}),'GET /api/shops':v({'shops':[{'name':'Hermes Shop','url':kit.shop_url,'stock':{'G1':2}}]}),'GET /api/forum':v({'data':[{'author':'Hermes Shop','role':'shop','ts':999}]}),'GET /api/inventory':v({'balance':99,'units':[{'sku':'G1'}]}),'GET /api/agents':v({'agents':[]})}
 logs=[{'at':1000,'text':'취나물','response_data':{'checkouts':[{'checkout_jwt':'signed'}]}},{'at':1001,'text':'결제함','data':{'tx_hash':'x'}}]
 r=run({'mode':'review','now':1002,'fixture':fixture,'customer_fixture':logs},kit)
 assert r['ok'] and (r['m'],r['i'],r['c'],r['s'],r['today'])==(1,1,1,1,1),r
 assert r['winners'][0]['lines']==1 and r['winners'][0]['posts_1h']==1 and r['balance']==99
 assert run({'mode':'inventory_units','sku':'G1','fixture':fixture},kit)['units']==[{'sku':'G1'}]
 fixture.update({'GET /.well-known/agent-card.json':v({'url':'https://test.trycloudflare.com/rpc'}),'POST /rpc':v({'result':{'status':{'state':'completed'}}})})
 r=run({'mode':'a2a','card_url':'https://test.trycloudflare.com/.well-known/agent-card.json','text':'안녕하세요','fixture':fixture},kit)
 assert r['ok'] and r['reply']['status']['state']=='completed'
 assert not run({'path':'/api/join','fixture':fixture},kit)['ok']
