from pathlib import Path
def test(run,kit):
 p=Path('tools/.deprecated/market_call@16/test.py')
 if not p.exists():p=Path('tools/market_call/test.py')
 ns={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns);ns['test'](run,kit)
 r=run({'mode':'inventory_units','sku':'G1','inventory_fixture':{'units':[{'sku':'G1','unit':'u1'},{'sku':'G2','unit':'u2'}]}},kit)
 assert r['ok'] and r['units']==[{'sku':'G1','unit':'u1'}],r
