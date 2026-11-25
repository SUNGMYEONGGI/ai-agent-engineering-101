import os,json,time,re,uuid
import httpx

def read(p,d):
 try:
  with open(p,encoding='utf8') as f:return json.load(f)
 except Exception:return d

def lines(p):
 try:
  with open(p,encoding='utf8') as f:return [json.loads(x) for x in f if x.strip()]
 except Exception:return []

def save(p,x):
 os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
 with open(p,'w',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False)

def run(args,kit):
 now=time.time(); text=args.get('text') or ''; data=args.get('data') or {}; ctx=args.get('context_id') or ''; who=args.get('claimed_from'); cp=args.get('catalog_path','public/catalog.json'); rp=args.get('reservations_path','public/reservations.jsonl'); lp=args.get('customers_path','customers.jsonl'); hp=args.get('holds_path','holds.json')
 def answer(reply,state='input_required',out=None,deal=None):
  os.makedirs(os.path.dirname(lp) or '.',exist_ok=True)
  with open(lp,'a',encoding='utf8') as f:f.write(json.dumps({'context_id':ctx,'claimed_from':who,'ts':now,'them':text,'you':reply,'deal':deal},ensure_ascii=False)+'\n')
  r={'reply':reply,'state':state}
  if out is not None:r['data']=out
  return r
 pm=data.get('payment_mandate'); cm=data.get('checkout_mandate'); order=data.get('order')
 if pm or cm:
  jwt=data.get('checkout_jwt') or ((cm or {}).get('mandate') or {}).get('checkout_jwt')
  if not all([pm,cm,order,jwt]):return answer('정산에 주문, checkout_jwt와 두 mandate가 모두 필요합니다.')
  body={'order':order,'checkout_jwt':jwt,'checkout_mandate':cm,'payment_mandate':pm}
  try:
   with httpx.Client(timeout=7) as c:
    r=c.post(kit.market+'/api/settle',json=body,headers={'Authorization':'Bearer '+kit.token('shop')})
    if r.status_code==503:r=c.post(kit.market+'/api/settle',json=body,headers={'Authorization':'Bearer '+kit.token('shop')})
   out=r.json()
   if r.status_code==200 and out.get('settled'):return answer('결제와 정산이 완료되었습니다. 감사합니다.','completed',out,{'settled':True})
   return answer('정산이 완료되지 않았습니다. 결제하셨다면 주문번호와 송금 내역을 알려주세요. 확인하겠습니다.','input_required',out,{'settled':False})
  except Exception:return answer('정산 서버 연결에 실패했습니다. 같은 결제 정보로 다시 요청해 주세요.')
 cat=read(cp,{'items':[]}); items=[x for x in cat.get('items',[]) if int(x.get('stock',0))>0]; rid=data.get('reservation_id'); reservations=lines(rp); res=next((x for x in reservations if rid and x.get('reservation_id')==rid and x.get('status','held')=='held' and float(x.get('expires_at',0))>now),None)
 if rid and not res:return answer('예약을 찾을 수 없거나 만료되었습니다.')
 words=[w.lower() for w in re.findall(r'[가-힣A-Za-z0-9]+',text) if len(w)>=2]; sku=data.get('sku'); candidates=[]
 for x in items:
  hay=(str(x.get('name',''))+' '+str(x.get('category',''))+' '+str(x.get('sku',''))).lower()
  if (res and x.get('sku')==res.get('sku') and (not res.get('grade') or res['grade']==x.get('grade'))) or (not res and (sku==x.get('sku') or any(w in hay or (len(w)>=2 and any(len(t)>=2 and t in w for t in re.findall(r'[가-힣A-Za-z0-9]+',hay))) for w in words))):candidates.append(x)
 candidates.sort(key=lambda x:int(x.get('price',0)))
 if not candidates:
  listing='\n'.join(f"{x.get('name')} {x.get('grade')}등급 {x.get('price')} credits" for x in items[:8]) or '현재 판매 가능한 상품이 없습니다.'
  return answer('안녕하세요. 현재 상품입니다.\n'+listing+'\n어떤 상품을 원하시나요?')
 try:
  if kit.testing: inv=args.get('_test_inventory',[])
  else:
   r=httpx.get(kit.market+'/api/inventory',headers={'Authorization':'Bearer '+kit.token('shop')},timeout=6); r.raise_for_status(); inv=r.json().get('units',[])
 except Exception:return answer('실재고 확인이 지연되고 있습니다. 잠시 후 다시 문의해 주세요.')
 holds={k:v for k,v in read(hp,{}).items() if v.get('expires',0)>now}; held_reserved={x.get('unit') or x.get('unit_id') for x in reservations if x.get('status','held')=='held' and float(x.get('expires_at',0))>now and x.get('reservation_id')!=rid}; chosen=None
 for item in candidates:
  allowed=set(item.get('units') or []); preferred=(res or {}).get('unit') or (res or {}).get('unit_id')
  units=sorted((u for u in inv if u.get('sku')==item.get('sku') and u.get('grade')==item.get('grade') and u.get('unit') in allowed and (not preferred or u.get('unit')==preferred)),key=lambda u:u.get('supplied_at',0))
  for u in units:
   uid=u['unit']; h=holds.get(uid)
   if uid not in held_reserved and (not h or (ctx and h.get('ctx')==ctx)):
    chosen=(item,u); break
  if chosen:break
 if not chosen:return answer('죄송합니다. 해당 상품은 현재 구매 가능한 실재고가 없습니다.')
 item,u=chosen; price=int(res.get('unit_price',item['price']) if res else item['price']); uid=u['unit']; cost=int(u.get('cost',0))
 if price-(price//100)-210<cost:return answer('죄송합니다. 해당 가격으로는 판매할 수 없습니다.')
 task=uuid.uuid4().hex; payload={'id':uuid.uuid4().hex,'shop':kit.name,'shop_url':kit.shop_url,'item':item['sku'],'price':price,'task':task,'currency':'credits','iat':int(now),'unit':uid,'claim':u['grade'],'warranty_hours':int(item.get('warranty_hours',0))}
 if u.get('cert'):payload['cert']=u['cert']
 jwt=kit.sign_jwt(payload,'shop'); holds[uid]={'ctx':ctx,'expires':now+180,'id':payload['id']}; save(hp,holds)
 if res:
  for x in reservations:
   if x.get('reservation_id')==rid:x['status']='sold'; x['unit']=uid
  os.makedirs(os.path.dirname(rp) or '.',exist_ok=True)
  with open(rp,'w',encoding='utf8') as f:
   for x in reservations:f.write(json.dumps(x,ensure_ascii=False)+'\n')
 expiry=u.get('expires_at'); detail=(' 유통기한 '+str(expiry)+'.') if expiry else ''
 reply=f"{item.get('name')} {u['grade']}등급, {price} credits, 보증 {payload['warranty_hours']}시간입니다.{detail} 결제용 checkout을 보내드립니다."
 return answer(reply,'completed',{'checkout_jwt':jwt}, {'checkout':payload['id'],'sku':item['sku'],'unit':uid,'price':price})
