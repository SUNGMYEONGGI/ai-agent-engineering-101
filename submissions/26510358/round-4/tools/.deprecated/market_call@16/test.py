from pathlib import Path
import time

def test(run,kit):
 p=Path('tools/.deprecated/market_call@14/test.py')
 if not p.exists():p=Path('tools/market_call/test.py')
 n={};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),n);n['test'](run,kit)
 now=time.time();p1=[{'seq':10,'kind':'settle','round':4,'ts':now-5,'data':{'shop':kit.name}}];p2=[{'seq':11,'kind':'settle','round':4,'ts':now-4,'data':{'shop':'other'}}]
 r=run({'mode':'metrics_full','now':now,'pages_fixture':{'-5000':p1,'10':p2},'logs_fixture':[]},kit)
 assert r['ok'] and r['hour']['market_settled']==2 and r['hour']['settled']==1 and r['today']==1 and r['last_seq']==11,r