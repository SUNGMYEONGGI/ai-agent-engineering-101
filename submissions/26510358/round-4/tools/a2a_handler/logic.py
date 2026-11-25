import os,json,time,re,uuid
import httpx

def read(p,d):
 try:
  with open(p,encoding='utf8') as f:return json.load(f)
 except Exception:return d

def lines(p):
 out=[]
 try:
  with open(p,encoding='utf8') as f:
   for x in f:
    if x.strip():
     try:out.append(json.loads(x))
     except Exception:pass
 except Exception:pass
 return out

def save(p,x):
 os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
 with open(p,'w',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False)

def kst(ts):
 try:return time.strftime('%m월 %d일 %H시',time.gmtime(float(ts)+9*3600))+'(KST)'
 except Exception:return str(ts)

STOP={'있나요','있습니까','주세요','얼마','가격','재고','상품','등급','구매','원해요','알려주세요','checkout','credits','안녕하세요'}

def want_grade(text,data):
 g=str(data.get('grade') or '').upper()
 if g in ('A','B','C'):return g
 m=re.search(r'(?<![A-Za-z])([ABCabc])\s*(등급|급)',text)
 return m.group(1).upper() if m else None

def run(args,kit):
 now=time.time(); text=args.get('text') or ''; data=args.get('data') or {}
 if not isinstance(data,dict):data={}
 ctx=args.get('context_id') or ''; who=args.get('claimed_from')
 cp=args.get('catalog_path','public/catalog.json'); rp=args.get('reservations_path','public/reservations.jsonl'); lp=args.get('customers_path','customers.jsonl'); hp=args.get('holds_path','holds.json')
 def answer(reply,state='input_required',out=None,deal=None):
  try:
   os.makedirs(os.path.dirname(lp) or '.',exist_ok=True)
   with open(lp,'a',encoding='utf8') as f:f.write(json.dumps({'context_id':ctx,'claimed_from':who,'ts':now,'them':text[:600],'you':reply[:600],'deal':deal},ensure_ascii=False)+'\n')
  except Exception:pass
  r={'reply':reply,'state':state}
  if out is not None:r['data']=out
  return r
 pm=data.get('payment_mandate'); cm=data.get('checkout_mandate'); order=data.get('order')
 if pm or cm:
  jwt=data.get('checkout_jwt') or ((cm or {}).get('mandate') or {}).get('checkout_jwt') if isinstance(cm,dict) else data.get('checkout_jwt')
  if not all([pm,cm,order,jwt]):return answer('정산에는 order, checkout_jwt, checkout_mandate, payment_mandate가 모두 필요합니다.')
  body={'order':order,'checkout_jwt':jwt,'checkout_mandate':cm,'payment_mandate':pm}
  if kit.testing:return answer('정산 테스트','completed',{'settled':True},{'settled':True,'test':True})
  try:
   with httpx.Client(timeout=6) as c:
    r=None
    for _ in range(3):
     r=c.post(kit.market+'/api/settle',json=body,headers={'Authorization':'Bearer '+kit.token('shop')})
     if r.status_code!=503:break
     time.sleep(1)
   try:out=r.json()
   except Exception:out={'status':r.status_code}
   if r.status_code==200 and (out.get('settled') or out.get('ok')):
    return answer('결제와 정산이 완료되었습니다. 감사합니다.','completed',out,{'settled':True,'order':order})
   return answer('정산이 완료되지 않았습니다('+str(out.get('error') or r.status_code)+'). 주문번호와 송금 tx_hash를 알려주시면 확인하겠습니다.','input_required',out,{'settled':False,'order':order})
  except Exception as e:return answer('정산 서버 연결에 실패했습니다. 같은 결제 정보로 다시 보내 주세요.','input_required',None,{'settled':False,'error':str(e)[:80]})
 cat=read(cp,{'items':[]}); items=[x for x in cat.get('items',[]) if int(x.get('stock',0) or 0)>0]
 rid=data.get('reservation_id'); reservations=lines(rp)
 res=next((x for x in reservations if rid and x.get('reservation_id')==rid and x.get('status','held')=='held' and float(x.get('expires_at',0) or 0)>now),None)
 if rid and not res:return answer('예약을 찾을 수 없거나 만료되었습니다. 원하시는 상품을 말씀해 주세요.')
 def listing(xs):
  return '\n'.join(f"- {x.get('name')} / {x.get('grade')}등급 / {x.get('price')} credits / 재고 {x.get('stock')}" for x in xs[:8])
 words=[w.lower() for w in re.findall(r'[가-힣A-Za-z0-9]+',text) if len(w)>=2 and w not in STOP]
 keys=set(words)|{w[:-1] for w in words if len(w)>=3 and re.match(r'[가-힣]',w)}
 sku=data.get('sku'); g=want_grade(text,data)
 if res:
  cands=[x for x in items if x.get('sku')==res.get('sku') and (not res.get('grade') or res['grade']==x.get('grade'))]
 else:
  cands=[]
  for x in items:
   hay=(str(x.get('name',''))+' '+str(x.get('category',''))).lower()
   if (sku and sku==x.get('sku')) or any(k and k in hay for k in keys):cands.append(x)
 if not cands:
  body=listing(items) or '현재 판매 가능한 상품이 없습니다.'
  return answer('안녕하세요, 헤르메스 상점입니다. 지금 파는 상품입니다.\n'+body+'\n원하시는 상품명(과 등급)을 말씀해 주세요.')
 if g and not res:
  same=[x for x in cands if x.get('grade')==g]
  if not same:
   return answer(f'죄송합니다. 요청하신 {g}등급은 지금 없습니다. 보유 중인 등급입니다.\n'+listing(sorted(cands,key=lambda x:int(x.get('price',0))))+'\n이 중 원하시면 상품명과 등급을 말씀해 주세요.')
  cands=same
 cands.sort(key=lambda x:int(x.get('price',0)))
 try:
  if kit.testing:inv=args.get('_test_inventory',[])
  else:
   r=httpx.get(kit.market+'/api/inventory',headers={'Authorization':'Bearer '+kit.token('shop')},timeout=6); r.raise_for_status(); inv=r.json().get('units',[])
 except Exception:return answer('실재고 확인이 지연되고 있습니다. 잠시 후 다시 문의해 주세요.')
 holds={k:v for k,v in read(hp,{}).items() if float(v.get('expires',0))>now}
 held_res={x.get('unit') or x.get('unit_id') for x in reservations if x.get('status','held')=='held' and float(x.get('expires_at',0) or 0)>now and x.get('reservation_id')!=rid}
 chosen=None
 for item in cands:
  allowed=set(item.get('units') or []); pref=(res or {}).get('unit') or (res or {}).get('unit_id')
  us=sorted((u for u in inv if u.get('sku')==item.get('sku') and u.get('grade')==item.get('grade') and u.get('unit') and u.get('unit') in allowed and (not pref or u.get('unit')==pref)),key=lambda u:u.get('supplied_at',0))
  for u in us:
   h=holds.get(u['unit'])
   if u['unit'] not in held_res and (not h or (ctx and h.get('ctx')==ctx)):chosen=(item,u);break
  if chosen:break
 if not chosen:return answer('죄송합니다. 해당 상품은 지금 구매 가능한 실재고가 없습니다.\n'+listing(items))
 item,u=chosen; uid=u['unit']; price=int(res.get('unit_price',item['price']) if res else item['price']); cost=int(u.get('cost',0) or 0)
 if not uid or price<=0:return answer('죄송합니다. 결제서를 만들 수 없습니다.')
 if price-(price//100)-210<cost:return answer('죄송합니다. 그 가격으로는 판매할 수 없습니다.')
 wh=int(item.get('warranty_hours',0) or 0)
 payload={'id':uuid.uuid4().hex,'shop':kit.name,'shop_url':kit.shop_url,'item':item['sku'],'price':price,'task':args.get('task_id') or uuid.uuid4().hex,'currency':'credits','iat':int(now),'unit':uid,'claim':u['grade'],'warranty_hours':wh}
 if u.get('cert'):payload['cert']=u['cert']
 jwt=kit.sign_jwt(payload,'shop')
 holds[uid]={'ctx':ctx,'expires':now+180,'id':payload['id']}; save(hp,holds)
 if res:
  for x in reservations:
   if x.get('reservation_id')==rid:x['status']='sold';x['unit']=uid
  os.makedirs(os.path.dirname(rp) or '.',exist_ok=True)
  with open(rp,'w',encoding='utf8') as f:
   for x in reservations:f.write(json.dumps(x,ensure_ascii=False)+'\n')
 exp=u.get('expires_at'); detail=(' 소비기한 '+kst(exp)+'.') if exp else ''
 reply=f"{item.get('name')} {u['grade']}등급(현재 재고 기준), {price} credits, 보증 {wh}시간입니다.{detail} 가게 지갑으로 서명한 checkout_jwt를 보내드립니다. 결제 후 order, checkout_mandate, payment_mandate(tx_hash, fee_tx_hash 포함)를 보내 주시면 바로 정산합니다."
 out={'checkout_jwt':jwt,'unit':uid,'sku':item['sku'],'grade':u['grade'],'price':price,'payee':kit.shop_url,'shop_wallet':kit.address('shop')}
 return answer(reply,'input_required',out,{'checkout':payload['id'],'sku':item['sku'],'unit':uid,'price':price,'grade':u['grade']})
