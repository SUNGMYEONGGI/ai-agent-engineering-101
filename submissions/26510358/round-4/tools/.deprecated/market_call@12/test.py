def test(run,kit):
 ledger=[{'kind':'settle','round':4,'ts':100,'data':{'shop':'https://shop.example','sku':'G12345678','grade':'B','amount':1000,'name':'계란'}},{'kind':'settle','round':4,'ts':101,'data':{'shop':'https://shop.example','sku':'G12345678','grade':'B','amount':1200}}]
 shops={'shops':[{'url':'https://shop.example','name':'가게'}]};board={'shops':[{'name':'가게','rank':1,'card':{'description':'진열'}}]};catalog={'items':[{'sku':'G12345678','name':'계란','grade':'B','price':990}]}
 r=run({'mode':'scan','ledger_fixture':ledger,'shops_fixture':shops,'board_fixture':board,'catalog_fixture':catalog},kit)
 assert r['ok'] and r['settles_per_shop']['가게']==2 and r['top15'][0]['median']==1100 and r['our_lines'][0]['gap_pct']==-10 and r['top3_cards'][0]['description']=='진열'
