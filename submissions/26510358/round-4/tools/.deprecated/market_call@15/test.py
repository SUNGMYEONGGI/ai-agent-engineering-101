from pathlib import Path
import time

def test(run,kit):
 p=Path('tools/.deprecated/market_call@14/test.py')
 if not p.exists():p=Path('tools/market_call/test.py')
 n={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),n);n['test'](run,kit)
 now=time.time();l=[{'kind':'settle','round':4,'ts':now-5,'data':{'shop':kit.name}},{'kind':'settle','round':4,'ts':now-4,'data':{'shop':'other'}}]
 r=run({'mode':'metrics_full','now':now,'ledger_fixture':l,'logs_fixture':[]},kit)
 assert r['ok'] and r['hour']['market_settled']==2 and r['hour']['settled']==1 and r['today']==1,r