import math,tempfile,os,json
def test(run,kit):
 os.makedirs('tmp/test',exist_ok=True)
 with tempfile.TemporaryDirectory(dir='tmp/test') as d:
  now=200000
  def unit(s,g,c,price,age,ident=None,exp=None):return {'unit':ident or s+g,'sku':s,'grade':g,'cost':c,'name':s,'list_price':price,'supplied_at':now-age*3600,'expires_at':exp or now+100000}
  units=[unit('known','B',1000,3000,1),unit('known','C',900,3000,1),unit('conflict','C',3000,4000,1),unit('old','C',1000,4000,24),unit('zero','B',1000,3000,1),unit('tea','B',2047,4000,24,'cheap',now+100),unit('tea','B',3008,4000,24,'dear',now+200),unit('egg','B',8740,10000,8,'egg1')]
  def sale(s,g,p):return {'round':4,'kind':'settle','data':{'sku':s,'grade':g,'amount':p}}
  ledger=[sale('known','B',2000),sale('known','C',1800),sale('conflict','B',3000),sale('old','B',5000),sale('tea','B',2724),sale('egg','B',7505)]
  p=d+'/catalog.json';rp=d+'/loss.json';a={'catalog_path':p,'reserve_path':rp,'inventory':units,'ledger_fixture':ledger,'now':now};r=run(a,kit);assert r['ok'],r
  by={(x['sku'],x['grade']):x for x in r['items']};assert by['known','B']['price']==1960 and by['known','C']['price']==1600
  assert ('conflict','C') not in by and r['excluded'][0]['sku']=='conflict'
  assert by['old','C']['price']==math.floor(4000*0.9**2) and by['zero','B']['price']==math.ceil(1210*100/99)+5
  assert by['tea','B']['units']==['cheap'] and json.load(open(p))['items']==r['items']
  a.update(loss_units=['egg1'],max_loss_per_day=30000);r=run(a,kit);assert r['ok'],r
  e=next(x for x in r['items'] if x['sku']=='egg');assert e['price']==7354 and e['units']==['egg1'];assert len(r['new_loss_reservations'])==1
  a['loss_units']=[];r=run(a,kit);assert r['ok'] and next(x for x in r['items'] if x['sku']=='egg')['price']==7354 and not r['new_loss_reservations']
  a['reserve_path']=d+'/other.json';a['loss_units']=['egg1'];a['max_loss_per_day']=100;r=run(a,kit);assert r['ok'] and next(x for x in r['items'] if x['sku']=='egg')['price']>7505 and not r['new_loss_reservations']
