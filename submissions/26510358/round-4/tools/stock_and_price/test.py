import math,tempfile,os,json
def test(run,kit):
 os.makedirs('tmp/test',exist_ok=True)
 with tempfile.TemporaryDirectory(dir='tmp/test') as d:
  now=200000;defunit=lambda sku,g,c,price,age:{'unit':sku+g,'sku':sku,'grade':g,'cost':c,'name':sku,'list_price':price,'supplied_at':now-age*3600,'expires_at':now+100000}
  units=[defunit('known','B',1000,3000,1),defunit('known','C',900,3000,1),defunit('conflict','C',3000,4000,1),defunit('old','C',1000,4000,24),defunit('zero','B',1000,3000,1)]
  def sale(s,g,p):return {'round':4,'kind':'settle','data':{'sku':s,'grade':g,'amount':p}}
  ledger=[sale('known','B',2000),sale('known','C',1800),sale('conflict','B',3000),sale('old','B',5000)]
  p=d+'/catalog.json';r=run({'catalog_path':p,'inventory':units,'ledger_fixture':ledger,'now':now},kit);assert r['ok'],r
  by={(x['sku'],x['grade']):x for x in r['items']};floor=math.ceil(1210*100/99)+5
  assert by['known','B']['price']==1960 and by['known','B']['price']>=floor
  assert by['known','C']['price']==1600
  assert ('conflict','C') not in by and r['excluded'][0]['sku']=='conflict'
  assert by['old','C']['price']==math.floor(4000*0.9**2)
  assert by['zero','B']['price']==floor
  assert json.load(open(p))['items']==r['items']
