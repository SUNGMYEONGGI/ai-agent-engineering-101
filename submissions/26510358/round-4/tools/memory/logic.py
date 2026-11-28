import time,json,datetime
from pathlib import Path
import httpx

def run(a,k):
 try:
  test=Path('tmp/test') if k.testing else Path('.')
  def save(name,text):
   test.mkdir(parents=True,exist_ok=True)
   (test/name).write_text(text,encoding='utf8')
  if a.get('mode')!='limits':
   text='RULES\n'+str(a.get('rules',''))+'\n\nNOW\n'+str(a.get('now',''))+'\n\nFAILED\n'+str(a.get('failed',''))
   text=text[:2490];save('notes.md',text)
   return {'ok':True,'written':True,'chars':len(text)}
  now=float(a['now']) if k.testing else time.time()
  def get(route,auth=False):
   if k.testing:return a['fixture'][route]
   r=httpx.get(k.market.rstrip('/')+route,headers={'Authorization':'Bearer '+k.token('shop')} if auth else {},timeout=8);r.raise_for_status();return r.json()
  inv=get('/api/inventory',True);units=inv['units'];book=inv['balance']-5000000+sum(int(u['cost']) for u in units)
  expiring=sum(int(u['cost']) for u in units if u.get('kind')=='food' and now<float(u.get('expires_at') or 0)<=now+86400)
  cursor=-5000;sales=0;sealed=0;seen=set();own={k.shop_url.rstrip('/').lower(),k.name.lower()}
  for _ in range(20):
   x=get('/api/ledger?after='+str(cursor));page=x if isinstance(x,list) else x.get('entries',x.get('ledger'))
   if not isinstance(page,list):raise ValueError('invalid ledger page')
   if not page:break
   for row in page:
    d=row.get('data') or {};seq=row['seq']
    if seq in seen or row.get('kind')!='settle' or row.get('round',4)!=4 or not now-86400<=float(row.get('ts',0))<=now+10 or str(d.get('shop_url') or d.get('shop') or '').rstrip('/').lower() not in own:continue
    seen.add(seq)
    if type(d.get('amount')) is int and d['amount']>0:sales+=d['amount']
    else:sealed+=1
   nxt=max(x['seq'] for x in page)
   if nxt<=cursor:raise ValueError('ledger cursor stalled')
   cursor=nxt
  else:raise ValueError('ledger page limit')
  try:owner=json.loads((test/'owner_limits.json').read_text(encoding='utf8'))
  except FileNotFoundError:owner={}
  inline=a.get('app_owner_limits') or {};cost=max(0,int(a.get('restock_unit_cost',0)))
  limits={}
  for key,want,default in [('max_pay_per_day',sales+30000,200000),('max_pay_per_call',cost*3,20000),('max_loss_per_day',expiring//2,30000)]:
   limits[key]=max(0,min(want,int(owner.get(key,default)),int(inline[key]) if key in inline else want))
  limits.update(reason=f'24h 확인 매출 {sales} (금액 비공개 {sealed}건 제외) + 30000; 우선 매입 단가 {cost} × 3; 24h 만료 식품 원가 {expiring} / 2; 소유자 상한 적용',set_at=datetime.datetime.fromtimestamp(now,datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M'))
  save('agent_limits.json',json.dumps(limits,ensure_ascii=False));return {'ok':True,'book':book,'balance':inv['balance'],'sales_24h':sales,'limits':limits}
 except Exception as e:return {'ok':False,'error':str(e)[:200]}