import os,json,time
import httpx

def load(path,default):
 try:
  with open(path,encoding='utf-8') as f:return json.load(f)
 except Exception:return default

def run(args,kit):
 text=args.get('text',''); data=args.get('data') or {}; now=time.time(); ctx=args.get('context_id','')
 cat=load('public/catalog.json',{'items':[]}); rid=data.get('reservation_id')
 res=None
 if rid:
  try:
   for line in open('public/reservations.jsonl',encoding='utf-8'):
    x=json.loads(line)
    if x.get('reservation_id')==rid and x.get('status','held')=='held' and float(x.get('expires_at',0))>now: res=x; break
  except Exception: pass
 if not res:return {'reply':'안녕하세요. reservation_id와 원하시는 상품을 보내주시면 확인하겠습니다.','state':'input_required'}
 item=next((x for x in cat.get('items',[]) if x.get('sku')==res.get('sku') and int(x.get('stock',0))>0),None)
 if not item:return {'reply':'죄송합니다. 현재 재고가 없습니다.','state':'rejected'}
 price=int(res.get('unit_price',item['price'])); task=rid+'-'+str(int(now))
 payload={'id':rid,'shop':kit.name,'shop_url':kit.shop_url,'item':item['sku'],'price':price,'task':task,'currency':'credits','iat':int(now),'unit':res.get('unit') or res.get('unit_id'),'claim':item.get('grade'),'warranty_hours':int(item.get('warranty_hours',0))}
 jwt=kit.sign_jwt(payload,'shop')
 with open('customers.jsonl','a',encoding='utf-8') as f:f.write(json.dumps({'context_id':ctx,'claimed_from':args.get('claimed_from'),'ts':now,'them':text,'you':'checkout','deal':{'sku':item['sku'],'price':price}},ensure_ascii=False)+'\n')
 pm=data.get('payment_mandate')
 if pm:
  body={'order':data.get('order'),'checkout_jwt':jwt,'checkout_mandate':data.get('checkout_mandate'),'payment_mandate':pm}
  with httpx.Client(timeout=8) as c:
   r=c.post(kit.market+'/api/settle',json=body,headers={'Authorization':'Bearer '+kit.token('shop')})
   if r.status_code==503:r=c.post(kit.market+'/api/settle',json=body,headers={'Authorization':'Bearer '+kit.token('shop')})
  out=r.json(); return {'reply':'정산 결과: '+str(out.get('settled',False)),'data':out,'state':'completed' if r.status_code==200 else 'rejected'}
 return {'reply':f"{item.get('name',item['sku'])} {item.get('grade','')}등급, {price} credits입니다. 결제용 checkout_jwt를 전달합니다.",'data':{'checkout_jwt':jwt},'state':'completed'}
