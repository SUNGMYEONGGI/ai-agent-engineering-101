import tempfile,os,json
def test(run,kit):
 os.makedirs('tmp/test',exist_ok=True)
 with tempfile.TemporaryDirectory(dir='tmp/test') as d:
  now=200000; cp=d+'/catalog.json';rp=d+'/res.json'
  u={'unit':'u1','sku':'fish','name':'고등어','grade':'C','cost':4000,'list_price':9900,'kind':'food','expires_at':now+1000,'supplied_at':now-90000}
  ledger={'data':[{'kind':'settle','round':4,'ts':now-100,'data':{'sku':'fish','grade':'C','amount':6000,'shop':'other'}}]}
  r=run({'inventory':[u],'ledger_fixture':ledger,'now':now,'catalog_path':cp,'reserve_path':rp},kit)
  assert r['ok'] and r['items'][0]['price']==5400 and r['items'][0]['units']==['u1']
  assert json.load(open(cp))['items'][0]['grade']=='C'
  u2=dict(u,unit='u2',cost=7000)
  r=run({'inventory':[u2],'ledger_fixture':ledger,'now':now,'catalog_path':cp,'reserve_path':rp,'loss_units':['u2'],'max_loss_per_day':30000},kit)
  assert r['ok'] and r['items'][0]['price']==5880 and r['new_loss_reservations'][0]['unit']=='u2'
  r=run({'inventory':[dict(u,expires_at=now-1)],'ledger_fixture':ledger,'now':now,'catalog_path':cp,'reserve_path':rp},kit)
  assert r['ok'] and not r['items']
