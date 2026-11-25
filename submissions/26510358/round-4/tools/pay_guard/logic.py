import json, os, time, httpx

def run(args, kit):
    role=args.get('role','shop')
    if role != 'shop': return {'ok':False,'error':'role_not_permitted'}
    credits=int(args.get('credits',0)); to=args.get('to'); data=args.get('data_hex','0x')
    if credits<=0 or credits>20000: return {'ok':False,'error':'amount_or_call_limit'}
    lim=args.get('app_owner_limits') or {}
    if credits>int(lim.get('per_call',10**18)): return {'ok':False,'error':'owner_call_limit'}
    if kit.testing:
        wei=1000000000000000; fee=420; bps=100
    else:
        try:
            r=httpx.get(kit.market+'/api/chain',timeout=10).json()['result']['summary']
            wei=int(r['credit_wei']); fee=int(r.get('network_fee_credits',0)); bps=int(r.get('market_fee_bps',0))
        except Exception:
            return {'ok':False,'error':'chain_unavailable'}
    path='pay_log.json'; logs=[]
    if os.path.exists(path):
        try: logs=json.load(open(path))
        except Exception: logs=[]
    now=time.time(); logs=[x for x in logs if now-x.get('ts',0)<86400]
    if sum(int(x.get('credits',0)) for x in logs)+credits>int(lim.get('per_day',10**18)):
        return {'ok':False,'error':'daily_limit'}
    if kit.testing: return {'ok':True,'tx_hash':'0x'+'0'*64,'credits':credits,'credit_wei':wei,'network_fee_credits':fee,'market_fee_bps':bps}
    tx=kit.pay(to,credits*wei,data,role='shop')
    logs.append({'ts':now,'credits':credits,'to':to}); json.dump(logs,open(path,'w'))
    return {'ok':True,'tx_hash':tx,'credits':credits,'credit_wei':wei,'network_fee_credits':fee,'market_fee_bps':bps}