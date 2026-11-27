def test(run,kit):
 inv={'balance':2000000,'units':[{'unit':'u','sku':'G1','grade':'B','cert':{},'cost':1200}]}
 q={'quote':'q','total':1200,'pay':{'to':'0x1','wei':'1200','data':'0x11'},'units':inv['units']}
 f={'GET /api/inventory':{'status':200,'json':inv},'POST /api/supply':{'status':402,'json':q},'GET /api/agents':{'status':200,'json':{'agents':[{'name':'peer','card_url':'https://peer.trycloudflare.com/.well-known/agent-card.json'}]}},'GET /.well-known/agent-card.json':{'status':200,'json':{'url':'https://peer.trycloudflare.com/a2a'}},'POST /a2a':{'status':200,'json':{'jsonrpc':'2.0','result':{'parts':[{'kind':'text','text':'계란 판매 중'}]}}}}
 r=run({'mode':'inventory_units','sku':'G1','fixture':f},kit);assert r['units']==inv['units'],r
 r=run({'path':'/api/supply','auth':True,'body':{'sku':'G1','qty':1},'fixture':f},kit);assert r['ok'] and r['http_status']==402 and r['quote']=='q' and r['total']==1200 and set(r['pay'])=={'to','wei','data'} and r['units'][0]['unit']=='u',r
 f['POST /api/supply']={'status':200,'json':{'total':1200,'units':inv['units']}}
 r=run({'path':'/api/supply','body':{'quote':'q','tx_hash':'0x2'},'fixture':f},kit);assert r['ok'] and r['total']==1200 and r['units'][0]['sku']=='G1',r
 r=run({'mode':'a2a','shop':'peer','fixture':f},kit);assert r['reply']['parts'][0]['text']=='계란 판매 중',r
