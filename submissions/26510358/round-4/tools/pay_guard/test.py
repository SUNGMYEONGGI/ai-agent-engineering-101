from pathlib import Path

def test(run,k):
 p=Path('tmp/test/pay_log.json');p.unlink(missing_ok=True)
 a={'credits':5,'to':'0x'+'1'*40,'operating_fixture':{'max_pay_per_call':9,'max_pay_per_day':8},'owner_fixture':{'max_pay_per_call':7,'max_pay_per_day':10},'inventory_fixture':{'balance':1100000},'chain':{'credit_wei':1000,'network_fee_credits':420,'market_fee_bps':100}}
 assert run(dict(a,credits=8),k)['error']=='call_limit'
 assert run(dict(a,inventory_fixture={'balance':1000004}),k)['error']=='balance_floor'
 r=run(a,k);assert r['ok'] and r['tx_hash']=='0x'+'0'*64 and r['credit_wei']==1000,r
 assert run(a,k)['error']=='daily_limit'
 assert run(dict(a,role='buyer'),k)['error']=='role_not_permitted'