import json, os, time

def run(args, kit):
    role=args.get('role','shop'); credits=int(args.get('credits',0)); to=args.get('to'); data=args.get('data_hex','0x')
    if credits<=0 or credits>20000: return {'ok':False,'error':'amount_or_call_limit'}
    lim=args.get('app_owner_limits')
    if isinstance(lim,dict):
        if credits>int(lim.get('per_call',10**18)): return {'ok':False,'error':'owner_call_limit'}
    path='pay_log.json'; logs=[]
    if os.path.exists(path):
        try: logs=json.load(open(path))
        except: logs=[]
    now=time.time(); logs=[x for x in logs if now-x.get('ts',0)<86400]
    if sum(x.get('credits',0) for x in logs)+credits>int((lim or {}).get('per_day',10**18)): return {'ok':False,'error':'daily_limit'}
    if kit.testing: return {'ok':True,'tx_hash':'0x'+'0'*64,'credits':credits}
    tx=kit.pay(to, credits*1000000000000000, data, role=role)
    logs.append({'ts':now,'credits':credits,'to':to}); json.dump(logs,open(path,'w'))
    return {'ok':True,'tx_hash':tx,'credits':credits}
