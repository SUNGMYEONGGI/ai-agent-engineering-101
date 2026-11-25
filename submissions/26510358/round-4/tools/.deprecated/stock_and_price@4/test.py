def test(run,kit):
 u={'unit':'u1','sku':'s','name':'백미 상등급','category':'식품','grade':'B','cost':1000,'list_price':3000,'expires_at':1234}
 x=run({'inventory':[u],'catalog_path':'tmp/test/stock/catalog.json','prices':[{'sku':'s','grade':'B','price':2000,'warranty_hours':3}]},kit)
 a=x['items'][0];assert all(k in a for k in ['sku','name','grade','price','stock','units','warranty_hours']);assert a['units']==['u1'] and a['grade']=='B' and a['price']==2000 and '상등급' not in a['name'] and a['expires_at']==1234