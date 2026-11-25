import json,os,time,httpx

def run(args,kit):
    text=args.get('text',''); data=args.get('data') or {}; ctx=args.get('context_id',''); now=time.time(); res=None
    try:
        for line in open('public/reservations.jsonl'):
            x=json.loads(line)
            if x.get('reservation_id')==data.get('reservation_id'): res=x
    except FileNotFoundError: pass
    if not res: return {'reply':'예약번호를 보내주시면 재고와 가격을 확인해 드리겠습니다.','state':'input_required'}
    if res.get('status')=='sold' or res.get('expires_at',0)<now: return {'reply':'죄송하지만 예약이 만료되었거나 이미 판매되었습니다.','state':'rejected'}
    if not res.get('unit_id'): return {'reply':'예약 상품의 재고 단위를 확인할 수 없습니다.','state':'rejected'}
    payload={'id':'checkout-'+str(int(now*1000)),'shop':kit.name,'shop_url':kit.shop_url,'item':res['sku'],'price':int(res['unit_price']),'task':ctx+'-'+str(int(now)),'currency':'credits','iat':int(now),'unit':res['unit_id'],'claim':res.get('grade','A'),'warranty_hours':int(res.get('warranty_hours',24))}
    jwt=kit.sign_jwt(payload,'shop'); pm=data.get('payment_mandate') or data.get('mandate'); reply='상품 확인했습니다. 아래 checkout_jwt로 결제해 주세요.'; state='input_required'
    if pm:
        body={'order':data.get('order'),'checkout_jwt':jwt,'checkout_mandate':data.get('checkout_mandate'),'payment_mandate':pm}
        r=httpx.post(kit.market+'/api/settle',headers={'Authorization':'Bearer '+kit.token('shop')},json=body,timeout=15)
        if r.status_code==503: r=httpx.post(kit.market+'/api/settle',headers={'Authorization':'Bearer '+kit.token('shop')},json=body,timeout=15)
        if r.json().get('settled'):
            reply='결제가 확인되어 주문이 정산되었습니다.'; state='completed'
            with open('public/reservations.jsonl','a') as f: f.write(json.dumps({**res,'status':'sold'})+'\n')
        else: reply='정산 확인이 되지 않았습니다. 결제 정보를 확인해 주세요.'
    with open('customers.jsonl','a') as f: f.write(json.dumps({'context_id':ctx,'claimed_from':args.get('claimed_from'),'ts':now,'them':text,'you':reply,'deal':res['unit_price']})+'\n')
    return {'reply':reply,'data':{'checkout_jwt':jwt},'state':state}
