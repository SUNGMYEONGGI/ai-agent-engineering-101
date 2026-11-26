import datetime,fcntl,json,math,os,re,time,uuid
from pathlib import Path
import httpx

NOUNS={'냉장고':['냉장고'],'우유':['우유'],'요거트':['요거트','요구르트'],'샴푸':['샴푸'],'치약':['치약'],'두부':['두부'],'계란':['계란','달걀','유정란'],'둥굴레차':['둥굴레차'],'보리차':['보리차'],'녹차':['녹차'],'홍차':['홍차'],'차':['둥굴레차','보리차','녹차','홍차','차'], '총각김치':['총각김치','알타리김치'],'김치':['김치'],'취나물':['취나물'],'시금치':['시금치'],'쌈채소':['쌈채소'],'콩나물':['콩나물'],'쌀':['쌀','백미'],'고등어':['고등어'],'사과':['사과'],'생수':['생수'],'고구마':['고구마'],'과자':['과자'],'타올':['키친타올','타올'],'커피':['커피']}
ORDER=sorted(NOUNS,key=len,reverse=True)
def tm(v):
 try:
  if not v:return 0
  return float(v)
 except (ValueError,TypeError):
  try:return datetime.datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
  except Exception:return 0
def checked_path(a,k,default,testing):
 p=Path(a.get(k,default))
 if testing:
  if p.is_absolute() or '..' in p.parts or p.parts[:2]!=('tmp','test'):raise ValueError('invalid test path')
 elif str(p)!=default:raise ValueError('invalid path')
 return p
def load(p,default):
 try:return json.loads(p.read_text(encoding='utf8'))
 except FileNotFoundError:return default
def api(kit,path,body=None):
 return httpx.request('POST' if body is not None else 'GET',kit.market.rstrip('/')+path,headers={'Authorization':'Bearer '+kit.token('shop')},json=body,timeout=8)
def say(s,data=None,state='input_required'):
 r={'reply':s,'state':state}
 if data is not None:r['data']=data
 return r
def settled(x):
 if not isinstance(x,dict):return False
 return x.get('settled') is True or x.get('status')=='settled' or x.get('state')=='settled' or settled(x.get('result')) or settled(x.get('data'))
def wanted(text):
 # Particles are delimiters only after a recognised noun, not inside nouns such as 사과.
 pat='|'.join(re.escape(x) for x in ORDER)
 text=re.sub(r'('+pat+r')(?:이랑|하고|와|과|랑)(?=\s|[가-힣A-Za-z])',r'\1,',text)
 chunks=re.split(r'[,，·/\n;]+|\s+(?:및|그리고|또는)\s+',text)
 out=[]
 for chunk in chunks:
  found=[]; occupied=[]
  for n in ORDER:
   for m in re.finditer(re.escape(n),chunk,re.I):
    if n=='차' and (m.start()>0 and re.match('[가-힣]',chunk[m.start()-1])):continue
    if any(m.start()<e and m.end()>s for s,e in occupied):continue
    occupied.append((m.start(),m.end()));found.append((m.start(),n))
  g=re.search(r'(?i)([abc])\s*(?:등급|급)',chunk)
  for _,n in sorted(found):
   if n not in [x[0] for x in out]:out.append((n,g.group(1).upper() if g else None))
 return out
def run(a,kit):
 t=time.time(); text=str(a.get('text') or ''); d=a.get('data') if isinstance(a.get('data'),dict) else {}
 try:
  cp=checked_path(a,'catalog_path','public/catalog.json',kit.testing); hp=checked_path(a,'holds_path','holds.json',kit.testing); log=checked_path(a,'customers_path','customers.jsonl',kit.testing); rp=checked_path(a,'reservations_path','public/reservations.jsonl',kit.testing)
  def work():
   keys=('order','checkout_jwt','checkout_mandate','payment_mandate')
   if any(k in d for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):
    p=d.get('payment_mandate'); core=p.get('payload',p) if isinstance(p,dict) else None
    if not all(d.get(k) for k in keys) or not isinstance(core,dict) or not all(core.get(k) for k in ('tx_hash','fee_tx_hash')):return say('결제하셨다면 다시 송금하지 마시고 주문서와 결제·수수료 거래가 포함된 mandate를 보내 주세요.')
    body={k:d[k] for k in keys}; r=api(kit,'/api/settle',body)
    if r.status_code==503:r=api(kit,'/api/settle',body)
    try:x=r.json()
    except Exception:x={}
    if r.is_success and settled(x):return say('정산이 완료되었습니다. 감사합니다.',{'order':d['order'],'settled':True},'completed')
    return say('정산 완료를 확인하지 못했습니다. 다시 송금하지 마시고 같은 주문 번호로 문의해 주세요.',{'order':d['order'],'settled':False,'settle_status':r.status_code})
   if re.search(r'환불|파손|보증\s*청구',text):return say('주문 번호와 원결제 거래 해시를 알려 주세요. 장부에서 확인하겠습니다. 추가 송금은 하지 마세요.')
   items=load(cp,{}).get('items',[])
   rid=d.get('reservation_id') or ((re.search(r'reservation_id\s*[:=]\s*([\w-]+)',text) or [None,None])[1])
   reservation=None
   if rid:
    try:
     for line in rp.read_text(encoding='utf8').splitlines():
      try:
       x=json.loads(line)
       if str(x.get('reservation_id',x.get('id','')))==str(rid):reservation=x
      except Exception:continue
    except FileNotFoundError:pass
    if not reservation or reservation.get('state',reservation.get('status'))!='held' or tm(reservation.get('expires_at'))<=t:return say('유효한 예약을 찾지 못했습니다. 예약 번호와 만료 시간을 확인해 주세요.')
   sku=str((reservation or {}).get('sku') or d.get('sku') or '')
   if not sku:
    m=re.search(r'\bG[0-9a-fA-F]{8}\b',text);sku=m.group() if m else ''
   grade=str(d.get('grade') or (reservation or {}).get('grade') or '').upper() or None
   requests=[('SKU '+sku,grade)] if sku else wanted(text)
   if not requests:return say('안녕하세요. 원하시는 상품명과 등급을 알려 주세요. 여러 품목이면 품목마다 결제서를 드립니다.')
   inv=a.get('inventory_fixture') if kit.testing else None
   if inv is None:
    r=api(kit,'/api/inventory');r.raise_for_status();inv=r.json()
   units=inv.get('units',[]) if isinstance(inv,dict) else []
   hp.parent.mkdir(parents=True,exist_ok=True)
   with open(hp,'a+',encoding='utf8') as f:
    fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
    try:holds=json.load(f)
    except Exception:holds={}
    if not isinstance(holds,dict):holds={}
    holds={k:v for k,v in holds.items() if isinstance(v,dict) and tm(v.get('expires_at',v.get('until',0)))>t}
    used=set(holds);results=[]; unavailable=[]; errors=[]
    for noun,localgrade in requests:
     target=grade or localgrade
     candidates=[x for x in items if isinstance(x,dict) and x.get('sku') and x.get('name') and type(x.get('price')) is int and x['price']>0 and x.get('stock',0)>0 and (x['sku'].lower()==sku.lower() if sku else any(word in x['name'] for word in NOUNS[noun]))]
     valid=[]
     for x in candidates:
      allowed=set(x.get('units',[]))
      for u in units:
       if u.get('sku')!=x['sku'] or str(u.get('grade','')).upper()!=str(x.get('grade','')).upper() or not u.get('unit') or u['unit'] not in allowed or u['unit'] in used:continue
       if tm(u.get('expires_at')) and tm(u['expires_at'])<=t:continue
       if x['price']<math.ceil((int(u.get('cost',0))+210)*100/99):continue
       if reservation and reservation.get('unit') and u['unit']!=reservation['unit']:continue
       valid.append((x,u))
     if target:
      have=sorted({x['grade'] for x,u in valid});valid=[(x,u) for x,u in valid if str(x['grade']).upper()==target]
      if not valid:
       errors.append(noun+' '+target+'등급은 없습니다'+(' (보유 등급: '+', '.join(have)+')' if have else ''));continue
     if not valid:unavailable.append(noun);continue
     if len(results)>=3:errors.append(noun+'은 한 번에 최대 3개까지만 결제서를 드려 별도 요청해 주세요');continue
     valid.sort(key=lambda z:(tm(z[1].get('expires_at')) or float('inf'),tm(z[1].get('supplied_at'))))
     x,u=valid[0];uid=u['unit'];used.add(uid);task=str(uuid.uuid4());cid=str(uuid.uuid4());price=x['price']
     if reservation and reservation.get('price') is not None:
      price=int(reservation['price'])
      if price<math.ceil((int(u.get('cost',0))+210)*100/99):errors.append(noun+' 예약 가격을 확인해 주세요');continue
     payload={'id':cid,'shop':kit.name,'shop_url':kit.shop_url,'item':x['sku'],'price':price,'task':task,'currency':'credits','iat':int(t),'unit':uid,'warranty_hours':x.get('warranty_hours',0)}
     if u.get('cert'):payload['cert']=u['cert']
     jwt=kit.sign_jwt(payload,'shop');holds[uid]={'expires_at':t+180,'checkout_id':cid,'task':task}
     expiry=tm(u.get('expires_at'));date=datetime.datetime.fromtimestamp(expiry,datetime.timezone(datetime.timedelta(hours=9))).strftime('%m월 %d일 %H:%M KST') if expiry else '표시 없음'
     results.append({'checkout_jwt':jwt,'unit':uid,'price':price,'sku':x['sku'],'name':x['name'],'grade':x['grade'],'expires_at':u.get('expires_at'),'warranty_hours':x.get('warranty_hours',0),'hold_until':int(t+180)})
    f.seek(0);f.truncate();json.dump(holds,f,ensure_ascii=False);f.flush();fcntl.flock(f,fcntl.LOCK_UN)
   msg=[]
   for x in results:
    date=datetime.datetime.fromtimestamp(tm(x['expires_at']),datetime.timezone(datetime.timedelta(hours=9))).strftime('%m월 %d일 %H:%M KST') if tm(x['expires_at']) else '표시 없음'
    msg.append('%s / %s등급 / %s credits / 소비기한 %s / 보증 %s시간. 결제서 180초 보류.'%(x['name'],x['grade'],x['price'],date,x['warranty_hours']))
   if unavailable:msg.append('와 '.join(unavailable)+'은(는) 없습니다.')
   msg+=errors
   data={'checkouts':results}
   if len(results)==1:data.update(results[0])
   return say('\n'.join(msg) or '재고를 확인하지 못했습니다.',data)
  result=work()
  log.parent.mkdir(parents=True,exist_ok=True)
  with open(log,'a',encoding='utf8') as f:f.write(json.dumps({'at':int(t),'text':text,'data':d,'claimed_from':a.get('claimed_from'),'task_id':a.get('task_id'),'context_id':a.get('context_id'),'reply':result},ensure_ascii=False,default=str)+'\n')
  return result
 except Exception as e:
  try:
   p=checked_path(a,'customers_path','customers.jsonl',kit.testing);p.parent.mkdir(parents=True,exist_ok=True)
   with open(p,'a',encoding='utf8') as f:f.write(json.dumps({'at':int(t),'text':text,'error':str(e)},ensure_ascii=False)+'\n')
  except Exception:pass
  return {'ok':False,'error':str(e),'state':'input_required','reply':'재고 확인에 문제가 생겼습니다. 잠시 후 다시 문의해 주세요.'}
