import os

def test(run,kit):
 p='tmp/test/pay_guard_test.json'
 try: os.remove(p)
 except FileNotFoundError: pass
 chain={'credit_wei':1000000000000000,'market_fee_bps':100,'network_fee_credits':420}
 a={'to':'0x'+'1'*40,'credits':5,'role':'shop','chain':chain,'log_path':p,'app_owner_limits':{'max_pay_per_call':10,'max_pay_per_day':8}}
 r=run(a,kit); assert r['ok'] and r['credit_wei']==chain['credit_wei'] and r['network_fee_credits']==420
 assert run(a,kit)['error']=='daily_limit'
 assert run(dict(a,credits=11),kit)['error']=='call_limit'
 assert run(dict(a,role='buyer'),kit)['error']=='role_not_permitted'
 assert run(dict(a,chain={}),kit)['error']=='chain_unavailable'