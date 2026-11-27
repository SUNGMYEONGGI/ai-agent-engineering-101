from pathlib import Path
p=Path('tools/.deprecated/market_call@16/logic.py')
if not p.exists():p=Path('tools/market_call/logic.py')
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),globals())
_old_units_run=run
def run(a,kit):
 if a.get('mode')!='inventory_units':return _old_units_run(a,kit)
 try:
  sku=a.get('sku');assert isinstance(sku,str) and sku
  inv=a['inventory_fixture'] if kit.testing else req(kit,'/api/inventory',True)
  return {'ok':True,'units':[u for u in inv.get('units',[]) if u.get('sku')==sku]}
 except Exception as e:return {'ok':False,'error':str(e)}
