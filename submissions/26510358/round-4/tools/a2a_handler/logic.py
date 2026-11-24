import json, os, time, httpx

def lines(path):
    try:
        with open(path,encoding='utf8') as f: return [json.loads(x) for x in f if x.strip()]
    except: return []
def save(path,xs):
    with open(path,'w',encoding='utf8') as f:
        for x in xs: f.write(json.dumps(x,ensure_ascii=False)+'\n')
def run(args,kit):
    now=time.time(); d=args.get('data') or {}; rid=d.get('reservation_id') or args.get('reservation_id')
    if d.get('payment_mandate') and d.get('checkout_mandate'):
        body={k:d[k] for k in ('order','checkout_jwt','checkout_mandate','payment_mandate') if k in d}
        with httpx.Client(timeout=15) as c:
            r=c.post(kit.market+'/api/settle',headers={'Authorization':'Bearer '+kit.token('shop')},json=body)
        try: out=r.json()
        except: out={}
        return {'reply':'정산 결과: '+str(r.status_code),'data':out,'state':'completed' if r.status_code==200 else 'input_required'}
    if rid:
        rs=lines('public/reservations.jsonl'); hit=next((x for x in rs if x.get('reservation_id')==rid and x.get('status','held')=='held' and float(x.get('expires_at',0))>now),None)
        if not hit: return {'reply':'예약을 찾을 수 없거나 만료되었습니다.','state':'rejected'}
        payload={'id':rid,'shop':kit.name,'shop_url':kit.shop_url,'item':hit['sku'],'price':int(hit['unit_price']),'task':rid,'currency':'credits','iat':int(now),'unit':hit.get('unit'),'warranty_hours':int(hit.get('warranty_hours',0))}
        jwt=kit.sign_jwt(payload,'shop'); hit['status']='sold'; save('public/reservations.jsonl',rs)
        with open('customers.jsonl','a',encoding='utf8') as f: f.write(json.dumps({'context_id':args.get('context_id'),'claimed_from':args.get('claimed_from'),'ts':now,'them':args.get('text',''),'you':'checkout','deal':rid},ensure_ascii=False)+'\n')
        return {'reply':'예약 상품입니다. checkout_jwt로 결제해 주세요.','data':{'checkout_jwt':jwt,'sku':hit['sku'],'price':hit['unit_price']},'state':'completed'}
    return {'reply':'안녕하세요. SKU, 등급, 가격 또는 예약 ID를 알려주세요.','state':'input_required'}
