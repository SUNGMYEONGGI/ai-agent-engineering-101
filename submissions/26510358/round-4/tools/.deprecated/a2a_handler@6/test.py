def test(run,kit):
 import os,json
 os.makedirs('public',exist_ok=True)
 with open('public/catalog.json','w',encoding='utf-8') as f: json.dump({'items':[{'sku':'x','name':'테스트','price':100,'stock':1}]},f)
 r=run({'text':'테스트','context_id':'c'},kit)
 assert r['state']=='completed' and r['data']['sku']=='x'
