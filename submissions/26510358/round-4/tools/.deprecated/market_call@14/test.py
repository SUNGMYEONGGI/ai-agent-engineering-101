def test(run,kit):
 now=100000
 ledger={'entries':[{'kind':'settle','round':4,'ts':now-10,'data':{'shop':'https://peer.trycloudflare.com','sku':'G1','grade':'B','amount':100}},{'kind':'settle','round':4,'ts':now-5,'data':{'shop':kit.shop_url,'sku':'G1','grade':'B','amount':90}}]}
 shops={'shops':[{'name':'Peer','url':'https://peer.trycloudflare.com','stock':{'G1':3}},{'name':kit.name,'url':kit.shop_url,'stock':{'G1':1}}]}
 agents={'agents':[{'name':'Peer','roles':['shop'],'card':'https://peer.trycloudflare.com/.well-known/agent-card.json'}]}
 card={'https://peer.trycloudflare.com/.well-known/agent-card.json':{'url':'https://peer.trycloudflare.com/','description':'안녕하세요'}}
 a=run({'mode':'scan','ledger_fixture':ledger,'shops_fixture':shops,'board_fixture':{'shops':[]},'catalog_fixture':{'items':[{'sku':'G1','grade':'B','price':90}]}},kit)
 assert a['ok'] and a['market_settles']==2 and a['our_lines'][0]['median']==95
 m=run({'mode':'metrics','now':now,'ledger_fixture':ledger,'logs_fixture':[{'ts':now-1,'text':'연결점검','checkout':True},{'ts':now-2,'text':'계란','checkout':True}]},kit)
 assert m['hour']['market_settled']==2 and m['hour']['msgs']==1 and m['hour']['checkouts']==1 and m['today']==1
 rev=run({'mode':'review','now':now,'ledger_fixture':ledger,'shops_fixture':shops,'agents_fixture':agents,'forum_fixture':[{'ts':now-1,'role':'shop','author':'Peer'}],'catalog_fixture':{'items':[]},'cards_fixture':card},kit)
 assert rev['ok'] and rev['winners'][0]['name']=='Peer' and rev['winners'][0]['forum_posts_1h']==1 and rev['winners'][0]['units']==3
 p=run({'mode':'a2a','now':now,'shop':'Peer','ledger_fixture':ledger,'shops_fixture':shops,'agents_fixture':agents,'cards_fixture':card,'response_fixture':{'result':{'status':{'state':'completed'}}}},kit)
 assert p['ok'] and p['response']['result']['status']['state']=='completed'
 bad=run({'mode':'a2a','now':now,'shop':'Other','ledger_fixture':ledger,'shops_fixture':shops,'agents_fixture':agents,'cards_fixture':card},kit)
 assert not bad['ok'] and bad.get('error')
 inv=run({'mode':'inventory','inventory_fixture':{'units':[{'sku':'G1','grade':'B','cost':50,'unit':'u'}]}},kit)
 assert inv['unit_count']==1 and inv['lots'][0]['min_cost']==50
