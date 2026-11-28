from pathlib import Path
import json

def test(run,k):
 assert run({'rules':'fees','now':'cards read','failed':'none'},k)['written']
 n=1795868402
 row={'seq':1,'ts':n,'kind':'settle','round':4,'data':{'shop':k.shop_url,'amount':5100}}
 fixture={'/api/inventory':{'balance':4800000,'units':[{'cost':10000,'kind':'food','expires_at':n+4000},{'cost':2000,'kind':'goods','expires_at':None}]},'/api/ledger?after=-5000':{'entries':[row]},'/api/ledger?after=1':{'entries':[]}}
 r=run({'mode':'limits','now':n,'fixture':fixture,'restock_unit_cost':4000,'app_owner_limits':{'max_pay_per_call':9000}},k)
 assert r['ok'] and r['book']==-188000 and r['sales_24h']==5100,r
 p=json.loads(Path('tmp/test/agent_limits.json').read_text());assert p['max_pay_per_call']==9000 and p['max_pay_per_day']==35100 and p['max_loss_per_day']==5000 and p['set_at']=='2026-11-28 21:20'