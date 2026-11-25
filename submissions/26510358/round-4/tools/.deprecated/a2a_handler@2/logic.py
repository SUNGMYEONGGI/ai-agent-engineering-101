import json,time,httpx

def read(p):
    try:
        with open(p,encoding='utf8') as f:return [json.loads(x) for x in f if x.strip()]
    except:return []
def write(p,xs):
    with open(p,'w',encoding='utf8') as f:
        for x in xs:f.write(json.dumps(x,ensure_ascii=False)+'\n')
def run(args,kit):
    d=args.get('data') or {}; now=time.time()
    if d.get('payment_mandate') and d.get('checkout_mandate'):
        body={k:d[k] for k in ('order','checkout_jwt','checkout_mandate','payment_mandate')}; out={}; status=0
        for _ in range(2):
            with httpx.Client(timeout=15) as c:
                r=c.post(kit.market+'/api/settle',headers={'Authorization':'Bearer '+kit.token('shop')},json=body)
            status=r.status_code
            try: out=r.json()
            except: out={'raw':r.text[:300]}
            if status!=503: break
        return {'reply':'정산 결과: '+str(status),'data':out,'state':'completed' if status==200 and out.get('settled',True) else 'input_required'}
    rid=d.get('reservation_id') or args.get('reservation_id')
    if not rid:return {'reply':'예약 ID를 보내 주세요.','state':'input_required'}
    rs=read('public/reservations.jsonl')
    hit=next((x for x in rs if x.get('reservation_id')==rid and x.get('status','held')=='held' and float(x.get('expires_at',0))>now),None)
    if not hit:return {'reply':'예약을 찾을 수 없거나 만료되었습니다.','state':'rejected'}
    if not kit.testing:
        try:
            with httpx.Client(timeout=8) as c:
                inv=c.get(kit.market+'/api/inventory',headers={'Authorization':'Bearer '+kit.token('shop')}).json()
            unit=hit.get('unit'); units=inv.get('units',[])
            ok=any(u.get('unit')==unit and u.get('sku')==hit.get('sku') for u in units) if unit else any(u.get('sku')==hit.get('sku') for u in units)
            if not ok:return {'reply':'해당 상품 재고가 없습니다.','state':'rejected'}
        except:return {'reply':'재고 확인에 실패했습니다.','state':'input_required'}
    payload={'id':rid,'shop':kit.name,'shop_url':kit.shop_url,'item':hit['sku'],'price':int(hit['unit_price']),'task':rid,'currency':'credits','iat':int(now),'unit':hit.get('unit'),'claim':hit.get('grade'),'warranty_hours':int(hit.get('warranty_hours',0))}
    jwt=kit.sign_jwt(payload,'shop'); hit['status']='sold'; write('public/reservations.jsonl',rs)
    with open('customers.jsonl','a',encoding='utf8') as f:f.write(json.dumps({'context_id':args.get('context_id'),'claimed_from':args.get('claimed_from'),'ts':now,'them':args.get('text',''),'you':'checkout','deal':rid},ensure_ascii=False)+'\n')
    return {'reply':'재고 확인 완료입니다. checkout_jwt로 결제 후 mandate를 보내 주세요.','data':{'checkout_jwt':jwt,'sku':hit['sku'],'price':hit['unit_price']},'state':'completed'}
