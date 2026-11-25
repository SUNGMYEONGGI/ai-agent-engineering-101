import json,time,httpx

def run(args,kit):
    text=args.get('text',''); data=args.get('data') or {}; ctx=args.get('context_id',''); now=time.time(); rid=data.get('reservation_id')
    try: cat=json.load(open('public/catalog.json')).get('items',[])
    except: cat=[]
    res=None
    if rid:
        try:
            for line in open('public/reservations.jsonl'):
                x=json.loads(line)
                if x.get('reservation_id')==rid: res=x
        except: pass
    if not res or res.get('status','held')!='held' or float(res.get('expires_at',0))<now:
        return {'reply':'예약번호와 상품 정보를 확인해 주세요. 유효한 예약만 결제 안내를 드립니다.','state':'input_required'}
    item=next((x for x in cat if x.get('sku')==res.get('sku')),None)
    if not item or int(item.get('stock',0))<1: return {'reply':'죄송합니다. 현재 해당 상품 재고가 없습니다.','state':'rejected'}
    price=int(res.get('unit_price',item['price']))
    payload={'id':rid,'shop':kit.name,'shop_url':kit.shop_url,'item':item['sku'],'price':price,'task':'r4-'+rid,'currency':'credits','iat':int(now),'unit':res.get('unit') or res.get('unit_id'),'claim':item.get('grade'),'warranty_hours':int(item.get('warranty_hours',0))}
    jwt=kit.sign_jwt(payload,'shop')
    if data.get('payment_mandate') and data.get('checkout_mandate'):
        body={'order':data.get('order'),'checkout_jwt':jwt,'checkout_mandate':data['checkout_mandate'],'payment_mandate':data['payment_mandate']}; headers={'Authorization':'Bearer '+kit.token('shop'),'Content-Type':'application/json'}
        for _ in range(2):
            r=httpx.post(kit.market+'/api/settle',json=body,headers=headers,timeout=10)
            if r.status_code!=503: break
        ok=r.status_code==200 and r.json().get('settled')
        return {'reply':'정산 완료되었습니다.' if ok else '정산이 완료되지 않았습니다. 같은 결제 자료로 다시 확인하겠습니다.','data':r.json() if r.status_code==200 else {},'state':'completed' if ok else 'input_required'}
    with open('customers.jsonl','a') as f: f.write(json.dumps({'context_id':ctx,'claimed_from':args.get('claimed_from'),'ts':now,'them':text,'you':'checkout issued','deal':rid},ensure_ascii=False)+'\n')
    return {'reply':'확인했습니다. 등급·보증을 반영한 결제 안내입니다. 아래 checkout_jwt로 결제해 주세요.','data':{'checkout_jwt':jwt,'sku':item['sku'],'price':price,'grade':item.get('grade'),'warranty_hours':item.get('warranty_hours',0)},'state':'completed'}
