import json,os,tempfile

def test(run,kit):
 os.makedirs('tmp/test',exist_ok=True)
 with tempfile.TemporaryDirectory(dir='tmp/test') as d:
  p=d+'/catalog.json'; u={'unit':'u-1','sku':'G1','name':'백미 상등급','category':'식품','grade':'B','cost':1000,'list_price':3000,'expires_at':2345}
  x=run({'catalog_path':p,'inventory':[u],'prices':[{'sku':'G1','grade':'B','price':2000,'warranty_hours':3}]},kit)
  assert x['ok'] and x['count']==1
  a=x['items'][0]; required=('sku','name','grade','price','stock','units','warranty_hours')
  assert all(k in a and a[k] is not None and a[k]!='' for k in required)
  assert a['units']==['u-1'] and a['grade']=='B' and a['price']==2000 and '상등급' not in a['name']
  units=[u,dict(u,unit='u-2',expires_at=1234),dict(u,sku='G2',unit='u-3',cost=3400),dict(u,grade='A',unit='u-4')]
  y=run({'catalog_path':p,'inventory':units,'featured':[{'sku':'G1','grade':'A'},{'sku':'G3','grade':'A'}]},kit)
  assert y['ok'] and y['count']==3 and [a['grade'] for a in y['items']]==['A','B','B']
  a=y['items'][1]; assert a['price']==2000 and a['warranty_hours']==3
  assert a['units']==['u-2','u-1'] and a['expires_at']==1234 and y['items'][2]['price']>=3647
  z=run({'catalog_path':p,'inventory':list(reversed(units))},kit)
  assert z==y
  with open(p,encoding='utf8') as f: assert json.load(f)['items']==y['items']
  assert run({'inventory':[]},kit)['ok'] is False