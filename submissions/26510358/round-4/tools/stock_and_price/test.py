import os
def test(run,kit):
 r=run({'items':[{'sku':'x','name':'테스트','grade':'A','price':100,'stock':1,'warranty_hours':24}]},kit); assert r['ok']
 assert os.path.exists('public/catalog.json')
