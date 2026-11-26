import json,math,os,re,time,statistics
from collections import defaultdict
from pathlib import Path
import httpx

def floor(u):
 c=int(u['cost']);return math.ceil((c+210)*100/99)+math.ceil(c*0.005)
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);q=str(p)+'.next'
 with open(q,'w',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False)
 os.replace(q,p)
def run(args,kit):
 try:
  p=Path(args.get('catalog_path','public/catalog.json'));rp=Path(args.get('reserve_path','loss_reservations.json'))
  if kit.testing:
   for f in (p,rp):
    if not str(f.resolve()).startswith(str(Path('tmp/test').resolve())+os.sep):raise ValueError('test path must be tmp/test')
  elif str(p)!='public/catalog.json' or str(rp)!='loss_reservations.json':raise ValueError('invalid path')
  try:old=json.loads(p.read_text(encoding='utf8')).get('items',[])
  except FileNotFoundError:old=[]
  try:reservations=json.loads(rp.read_text(encoding='utf8'))
  except FileNotFoundError:reservations=[]
  if not isinstance(reservations,list):raise ValueError('invalid reservations')
  if kit.testing:units=args['inventory'];ledger=args['ledger_fixture'];now=args.get('now',time.time())
  else:
   h={'Authorization':'Bearer '+kit.token('shop')};r=httpx.get(kit.market.rstrip('/')+'/api/inventory',headers=h,timeout=12);r.raise_for_status();units=r.json()['units']
   r=httpx.get(kit.market.rstrip('/')+'/api/ledger?after=-500',timeout=12);r.raise_for_status();ledger=r.json();now=time.time()
  if isinstance(ledger,dict):ledger=ledger.get('entries',ledger.get('ledger',[]))
  if not isinstance(ledger,list) or not isinstance(units,list):raise ValueError('inventory/ledger invalid')
  sales=defaultdict(list)
  for e in ledger:
   if e.get('kind')!='settle' or e.get('round',4)!=4:continue
   d=e.get('data') or {};sku=d.get('sku') or d.get('item');grade=d.get('grade');price=d.get('amount',d.get('price'))
   if isinstance(sku,str) and grade in ('A','B','C') and isinstance(price,(int,float)) and price>0:sales[(sku,grade)].append(price)
  groups=defaultdict(list)
  for u in units:
   if u.get('sku') and u.get('grade') and u.get('unit') and isinstance(u.get('cost'),(int,float)) and (not u.get('expires_at') or u['expires_at']>now):groups[(u['sku'],u['grade'])].append(u)
  previous={(x['sku'],x['grade']):x for x in old};priority={}
  for x in args.get('featured',[])+old:priority.setdefault((x['sku'],x['grade']),len(priority))
  day=time.strftime('%Y-%m-%d',time.gmtime(now+32400));cap=min(30000,max(0,int(args.get('max_loss_per_day',30000))));spent=sum(int(x['loss']) for x in reservations if x.get('day')==day)
  allowed=set(args.get('loss_units',[]));allowed.update(x['unit'] for x in reservations if x.get('day')==day and x.get('active'))
  out=[];excluded=[];added=[]
  for sku,grade in sorted(groups,key=lambda k:(priority.get(k,len(priority)),k)):
   us=groups[(sku,grade)];us.sort(key=lambda u:(u.get('expires_at') or float('inf'),u.get('supplied_at') or 0));first=us[0];low=floor(first)
   ps=sales.get((sku,grade),[]);b=sales.get((sku,'B'),[]);med=statistics.median(ps) if ps else None;bmed=statistics.median(b) if b else None
   if med:desired=math.floor(med*0.98)
   elif not any(k[0]==sku for k in sales):desired=low
   else:
    base=int(first.get('list_price') or low);age=max(0,(now-float(first.get('supplied_at') or now))/3600);desired=math.floor(base*0.9**math.floor(age/12))
   price=max(low,desired);loss_used=False
   if med and first['unit'] in allowed and now-float(first.get('supplied_at') or now)>=21600 and low>med:
    candidate=max(math.ceil(med*0.97),math.floor(med*0.98));loss=low-candidate
    prior=next((x for x in reservations if x.get('day')==day and x.get('unit')==first['unit'] and x.get('active')),None)
    if prior and loss<=int(prior['loss']):price=candidate;loss_used=True
    elif not prior and loss>0 and spent+loss<=cap:
     price=candidate;loss_used=True;rec={'day':day,'unit':first['unit'],'sku':sku,'grade':grade,'loss':loss,'price':price,'active':True};reservations.append(rec);added.append(rec);spent+=loss
   if grade=='C' and bmed and price>math.floor(0.8*bmed):
    c=math.floor(0.8*bmed)
    if low>c and not loss_used:excluded.append({'sku':sku,'grade':grade,'floor':low,'cap':c,'reason':'C등급 상한이 원가 하한보다 낮음'});continue
    if not loss_used:price=c
   selected=[]
   for u in us:
    if floor(u)>price and not (loss_used and u['unit']==first['unit']):break
    selected.append(u)
   name=re.sub(r'(?:1\+\+|1\+|특|상|A|B|C)\s*등급','',first.get('name') or sku,flags=re.I).strip().strip('/').strip() or sku
   out.append({'sku':sku,'name':name,'category':first.get('category') or '', 'grade':grade,'price':price,'stock':len(selected),'units':[u['unit'] for u in selected],'expires_at':min((u['expires_at'] for u in selected if u.get('expires_at')),default=None),'warranty_hours':max(0,int(previous.get((sku,grade),{}).get('warranty_hours') or 0))})
  if args.get('mode')!='preview':
   if added:save(rp,reservations)
   save(p,{'items':out})
  return {'ok':True,'count':len(out),'items':out,'excluded':excluded,'loss_reserved_today':spent,'new_loss_reservations':added,'published':args.get('mode')!='preview'}
 except Exception as e:return {'ok':False,'error':type(e).__name__+': '+str(e)[:230]}
