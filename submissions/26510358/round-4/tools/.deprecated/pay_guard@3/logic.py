import json, os, time, httpx

def run(args,kit):
 if args.get('role','shop')!='shop': return {'ok':False,'error':'role_not_permitted'}
 try: n=int(args.get('credits',0))
 except (ValueError,TypeError): return {'ok':False,'error':'invalid_amount'}
 lim=args.get('app_owner_limits') or {}; call=int(lim.get('max_pay_per_call',20000)); day=int(lim.get('max_pay_per_day',200000))
 if n<=0 or n>min(20000,call): return {'ok':False,'error':'call_limit'}
 try:
  c=args['chain'] if kit.testing else httpx.get(kit.market.rstrip('/')+'/api/chain',timeout=10).json()
  wei=int(c['credit_wei']); fee=int(c['network_fee_credits']); bps=int(c['market_fee_bps']); assert wei>0 and fee>=0 and bps>=0
 except Exception: return {'ok':False,'error':'chain_unavailable'}
 p=args.get('log_path','pay_log.json'); now=time.time()
 try:
  with open(p) as f: logs=json.load(f)
 except FileNotFoundError: logs=[]
 except Exception: return {'ok':False,'error':'log_unreadable'}
 logs=[x for x in logs if now-x.get('ts',0)<86400]
 if sum(int(x['credits']) for x in logs)+n>day: return {'ok':False,'error':'daily_limit'}
 entry={'ts':now,'credits':n,'to':args.get('to'),'data_hex':args.get('data_hex','0x'),'state':'pending'}
 if any(x.get('state')=='pending' and x.get('to')==entry['to'] and x.get('data_hex')==entry['data_hex'] for x in logs): return {'ok':False,'error':'pending_duplicate'}
 logs.append(entry); os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
 with open(p,'w') as f: json.dump(logs,f)
 try: tx=kit.pay(entry['to'],n*wei,entry['data_hex'],role='shop')
 except Exception as e: return {'ok':False,'error':'payment_uncertain','detail':str(e)[:200]}
 entry.update(state='sent',tx_hash=tx)
 with open(p,'w') as f: json.dump(logs,f)
 return {'ok':True,'tx_hash':tx,'credits':n,'credit_wei':wei,'network_fee_credits':fee,'market_fee_bps':bps}