import tempfile,os,json
from pathlib import Path

def test(run,kit):
 os.makedirs('tmp/test',exist_ok=True)
 with tempfile.TemporaryDirectory(dir='tmp/test') as d:
  p=str(Path(d)/'catalog.json');rp=str(Path(d)/'loss.json');now=1795803873
  def unit(i,c,t,**kw):return dict(unit=i,sku='Gab7c8b3d',grade='B',name='계란 20구',kind='food',cost=c,expires_at=now+t,supplied_at=now-100,**kw)
  ret=run({'catalog_path':p,'reserve_path':rp,'now':now,'inventory':[unit('u-expired',100,-1),unit('u-old',5396,50000),unit('u-costly',7069,60000),unit('u-new',5167,70000),unit('u-sold',1,80000,sold=True)],'ledger_fixture':[{'kind':'settle','round':4,'data':{'sku':'Gab7c8b3d','grade':'B','amount':7372}}]},kit)
  assert ret['ok'] and ret['published'] and ret['count']==1,ret
  item=ret['items'][0]
  assert (item['sku'],item['name'],item['grade'],item['price'],item['stock'],item['units'],item['warranty_hours'])==('Gab7c8b3d','계란 20구','B',7224,2,['u-old','u-new'],0),item
  assert [r['unit'] for r in ret['excluded']]==['u-costly']
  assert json.loads(Path(p).read_text())['items']==[item]
  return {'ok':True}
