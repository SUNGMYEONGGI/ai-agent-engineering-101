import json, time, hashlib, httpx

def load(p,d):
    try:
        with open(p,encoding='utf-8') as f:return json.load(f)
    except:return d

def log(o):
    with open('customers.jsonl','a',encoding='utf-8') as f:f.write(json.dumps(o,ensure_ascii=False,separators=(',',':'))+'\n')

def run(args,kit):
    now=time.time(); text=args.get('text',''); data=args.get('data') or {}; cid=args.get('context_id','')
    if data.get('tx_hash') and data.get('fee_tx_hash') and data.get('checkout_jwt'):
        body={k:data[k] for k in ('order','checkout_jwt','checkout_mandate','payment_mandate') if k in data}
        if 'payment_mandate' in body: body['payment_mandate']['mandate'].update({'tx_hash':data['tx_hash'],'fee_tx_hash':data['fee_tx_hash']})
        out=None
        for _ in range(2):
            r=httpx.post(kit.market+'/api/settle',json=body,headers={'Authorization':'Bearer '+kit.token('shop')},timeout=8); out=r.json()
            if r.status_code!=503: break
        log({'context_id':cid,'claimed_from':args.get('claimed_from'),'ts':now,'them':data,'you':'settle','deal':out})
        return {'reply':'정산 결과: '+json.dumps(out,ensure_ascii=False),'data':out,'state':'completed' if out.get('settled') else 'rejected'}
    cat=load('public/catalog.json',{'items':[]}); chosen=None
    rid=data.get('reservation_id')
    if rid:
        try:
            with open('public/reservations.jsonl',encoding='utf-8') as f:
                for line in f:
                    x=json.loads(line)
                    if x.get('reservation_id')==rid and x.get('status','held')=='held' and x.get('expires_at',now)>now: chosen=x; break
        except: pass
        if not chosen:return {'reply':'예약이 만료되었거나 이미 판매되었습니다.','state':'rejected'}
    if chosen: sku,price,unit=chosen.get('sku'),chosen.get('unit_price'),chosen.get('unit')
    else:
        it=next((x for x in cat['items'] if x.get('stock',0)>0 and (x.get('sku') in text or x.get('name') in text)),None)
        if not it:return {'reply':'상품명 또는 SKU를 말씀해 주세요.','state':'input_required'}
        sku,price,unit=it['sku'],it['price'],it.get('unit')
    payload={'id':'checkout-'+hashlib.sha256((cid+str(now)+sku).encode()).hexdigest()[:16],'shop':kit.name,'shop_url':kit.shop_url,'item':sku,'price':int(price),'task':cid+'-'+str(int(now)),'currency':'credits','iat':int(now),'unit':unit,'warranty_hours':chosen.get('warranty_hours',0) if chosen else 0}
    jwt=kit.sign_jwt(payload,'shop'); log({'context_id':cid,'claimed_from':args.get('claimed_from'),'ts':now,'them':text,'you':'checkout','deal':payload})
    return {'reply':f'SKU {sku}, 가격 {price} credits입니다. 결제 후 tx_hash와 fee_tx_hash를 보내주세요.','data':{'checkout_jwt':jwt,'sku':sku,'price':price},'state':'completed'}
