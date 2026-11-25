import json,time,httpx,os

def lines(path):
    try:
        with open(path) as f: return [json.loads(x) for x in f if x.strip()]
    except: return []

def run(args,kit):
    text=args.get('text',''); data=args.get('data') or {}; ctx=args.get('context_id',''); now=time.time()
    cat=lines('public/catalog.json') if False else json.load(open('public/catalog.json')).get('items',[])
    rid=data.get('reservation_id'); res=None
    if rid:
        for x in lines('public/reservations.jsonl'):
            if x.get('reservation_id')==rid: res=x
        if not res or res.get('status','held')!='held' or float(res.get('expires_at',0))<now:
            return {'reply':'예약번호가 만료되었거나 이미 처리되었습니다.','state':'input_required'}
    sku=(res or {}).get('sku') or data.get('sku')
    item=next((x for x in cat if x.get('sku')==sku),None)
    if not item or int(item.get('stock',0))<1:
        return {'reply':'죄송합니다. 현재 해당 상품 재고가 없습니다.','state':'rejected'}
    price=int((res or {}).get('unit_price',item.get('price',0)))
    unit=(res or {}).get('unit') or (res or {}).get('unit_id')
    payload={'id':rid or 'q-'+str(int(now*1000)),'shop':kit.name,'shop_url':kit.shop_url,'item':sku,'price':price,'task':'r4-'+str(rid or ctx or int(now)),'currency':'credits','iat':int(now),'unit':unit,'claim':item.get('grade'),'warranty_hours':int(item.get('warranty_hours',0))}
    jwt=kit.sign_jwt(payload,'shop')
    with open('customers.jsonl','a') as f: f.write(json.dumps({'context_id':ctx,'claimed_from':args.get('claimed_from'),'ts':now,'them':text,'you':'checkout issued','deal':rid or sku},ensure_ascii=False)+'\n')
    if data.get('payment_mandate') and data.get('checkout_mandate'):
        body={'order':data.get('order'),'checkout_jwt':jwt,'checkout_mandate':data['checkout_mandate'],'payment_mandate':data['payment_mandate']}; h={'Authorization':'Bearer '+kit.token('shop'),'Content-Type':'application/json'}
        for _ in range(2):
            r=httpx.post(kit.market+'/api/settle',json=body,headers=h,timeout=10)
            if r.status_code!=503: break
        out=r.json() if r.status_code==200 else {}
        ok=r.status_code==200 and out.get('settled') is True
        if ok and rid:
            rs=lines('public/reservations.jsonl')
            for x in rs:
                if x.get('reservation_id')==rid: x['status']='sold'; x['sold_at']=now
            with open('public/reservations.jsonl','w') as f:
                for x in rs: f.write(json.dumps(x,ensure_ascii=False)+'\n')
        return {'reply':'정산 완료되었습니다.' if ok else '정산이 완료되지 않았습니다. 같은 결제 자료를 다시 보내 주세요.','data':out,'state':'completed' if ok else 'input_required'}
    return {'reply':'확인했습니다. 아래 서명된 checkout_jwt로 결제해 주세요.','data':{'checkout_jwt':jwt,'sku':sku,'price':price,'grade':item.get('grade'),'warranty_hours':item.get('warranty_hours',0)},'state':'completed'}
