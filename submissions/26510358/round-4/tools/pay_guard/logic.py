import json,re,time,fcntl,datetime
from pathlib import Path
import httpx

def run(a,k):
 def fail(s):return {'ok':False,'error':s}
 try:
  if a.get('role','shop')!='shop':return fail('role_not_permitted')
  n=a.get('credits');to=a.get('to','');data=a.get('data_hex','0x')
  if type(n) is not int or n<=0 or not re.fullmatch('0x[0-9a-fA-F]{40}',to) or not re.fullmatch('0x(?:[0-9a-fA-F]{2})*',data):return fail('invalid_payment')
  now=time.time();base=Path('tmp/test') if k.testing else Path('.')
  def read(name):return json.loads((base/name).read_text())
  def get(path,auth=False):
   r=httpx.get(k.market.rstrip('/')+path,headers={'Authorization':'Bearer '+k.token('shop')} if auth else {},timeout=8);r.raise_for_status();return r.json()
  op=a['operating_fixture'] if k.testing else read('agent_limits.json')
  if not k.testing:
   t=datetime.datetime.strptime(op['set_at'],'%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9))).timestamp()
   if not -60<=now-t<=10800:return fail('stale_operating_limits')
  try:owner=a.get('owner_fixture',{}) if k.testing else read('owner_limits.json')
  except FileNotFoundError:owner={}
  inline=a.get('app_owner_limits') or {}
  def lim(key,default):return min(int(op[key]),int(owner.get(key,default)),int(inline.get(key,owner.get(key,default))))
  if n>lim('max_pay_per_call',20000) or n>20000:return fail('call_limit')
  day=lim('max_pay_per_day',200000)
  c=a['chain'] if k.testing else get('/api/chain');wei=int(c['credit_wei']);fee=int(c['network_fee_credits']);bps=int(c['market_fee_bps'])
  if not (wei>0 and fee>=0 and 0<=bps<=10000):return fail('chain_unavailable')
  inv=a['inventory_fixture'] if k.testing else get('/api/inventory',True)
  if int(inv['balance'])-n-fee-int(inv.get('storage_due_with_next_lot',0))<1000000:return fail('balance_floor')
  base.mkdir(parents=True,exist_ok=True)
  with (base/'pay_log.json').open('a+',encoding='utf8') as f:
   fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);raw=f.read();logs=json.loads(raw) if raw else []
   logs=[x for x in logs if now-float(x['ts'])<86400]
   if sum(int(x['credits']) for x in logs)+n>day:return fail('daily_limit')
   if any(x.get('state')=='pending' and str(x['to']).lower()==to.lower() and str(x['data_hex']).lower()==data.lower() for x in logs):return fail('pending_duplicate')
   def store():f.seek(0);f.truncate();json.dump(logs,f);f.flush();__import__('os').fsync(f.fileno())
   row={'ts':now,'credits':n,'to':to,'data_hex':data,'state':'pending'};logs.append(row);store()
   try:tx=k.pay(to,n*wei,data,role='shop')
   except Exception:return fail('payment_uncertain')
   row.update(state='sent',tx_hash=tx);store()
  return {'ok':True,'tx_hash':tx,'credits':n,'credit_wei':wei,'network_fee_credits':fee,'market_fee_bps':bps}
 except Exception as e:return fail(str(e)[:160])