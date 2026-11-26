import base64, datetime, fcntl, json, os, re, time, uuid
import httpx

STOP=set('가정용 새제품 제품 상품 배송 설치 최종 가격 조건 판매 가능 확인 부탁 문의 재고 지금 현재 오늘 아침용 아이 대용량 소포장 묶음 소비기한 기한 유효 서명 결제 한정 단단한 국산 국내산 정식수입 상온보관 당일수확 무가당 플레인 고단백 관리 안녕하세요 주세요 찾습니다 있나요 알려주세요 판매가능 쇼핑 냉장 냉동 할인 등급 정품 가정용'.split())
ALIASES={'계란':('유정란','달걀','계란'),'달걀':('유정란','달걀','계란'),'우유':('우유',),'요거트':('요거트','요구르트'),'두부':('두부','연두부','순두부','멸균두부'),'차':('둥굴레차','보리차','녹차','홍차','우롱차'),'김치':('김치','총각김치','무김치','배추김치'),'냉장고':('냉장고','소형냉장고','양문형냉장고'),'커피':('커피',)}

def words(s):
    out=set()
    for w in re.findall(r'[가-힣a-z0-9]+',str(s).lower()):
        out.add(w)
        for end in ('으로','에서','에게','부터','까지','하고','이랑','이나','와','과','을','를','은','는','도','이','가','랑'):
            if w.endswith(end) and len(w)-len(end)>=2:
                out.add(w[:-len(end)])
    return {w for w in out if (len(w)>=2 or w in ALIASES) and w not in STOP and not w.isdigit() and not re.fullmatch(r'[abc](?:등급|급)|\d+[a-z가-힣]+',w)}

def fields(x):
    if isinstance(x,dict):
        for k,v in x.items():
            if k=='units' and isinstance(v,list):
                yield from (u for u in v if isinstance(u,dict))
            elif isinstance(v,(list,dict)):
                yield from fields(v)
    elif isinstance(x,list):
        for v in x: yield from fields(v)

def load(p,default):
    try:
        with open(p,encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError: return default

def rows(p):
    try:
        with open(p,encoding='utf-8') as f:
            for line in f:
                try:
                    x=json.loads(line)
                    if isinstance(x,dict): yield x
                except ValueError: continue
    except FileNotFoundError: pass

def stamp(v):
    if not v: return 0
    try: return float(v)
    except (ValueError,TypeError): return datetime.datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()

def info(i):
    expiry=stamp(i.get('expires_at'))
    when=datetime.datetime.fromtimestamp(expiry,datetime.timezone(datetime.timedelta(hours=9))).strftime('%m월 %d일 %H:%M KST') if expiry else '표시 없음'
    return f"{i['name']} / {i['grade']}등급 / {i['price']} credits / 소비기한 {when} / 보증 {i.get('warranty_hours',0)}시간"

def market(kit,path,body=None):
    h={'Authorization':'Bearer '+kit.token('shop')}
    return httpx.request('POST' if body is not None else 'GET',kit.market.rstrip('/')+path,headers=h,json=body,timeout=7)

def answer(a,kit,d,t):
    text=str(a.get('text') or '')
    def say(s,state='input_required',data=None):
        ret={'reply':s,'state':state}
        if data is not None: ret['data']=data
        return ret
    keys=('order','checkout_jwt','checkout_mandate','payment_mandate')
    if any(k in d for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):
        p=d.get('payment_mandate')
        core=p.get('payload',p) if isinstance(p,dict) else None
        if not all(d.get(k) for k in keys) or (isinstance(core,dict) and not all(core.get(k) for k in ('tx_hash','fee_tx_hash'))):
            return say('결제하셨다면 중복 송금하지 마시고 order, checkout_jwt, checkout_mandate, 결제·수수료 tx hash가 포함된 payment_mandate를 보내 주세요.')
        body={k:d[k] for k in keys}
        r=market(kit,'/api/settle',body)
        if r.status_code==503: r=market(kit,'/api/settle',body)
        try: x=r.json()
        except ValueError: x={}
        def settled(z):
            return isinstance(z,dict) and (z.get('settled') is True or z.get('status')=='settled' or z.get('state')=='settled' or settled(z.get('result')) or settled(z.get('data')))
        if r.is_success and settled(x):
            return say('정산이 완료되었습니다. 감사합니다.','completed',{'order':d['order'],'settled':True})
        return say('정산 완료를 확인하지 못했습니다. 다시 송금하지 마시고 같은 주문 번호와 거래 내역으로 문의해 주세요.',data={'order':d['order'],'settled':False,'settle_status':r.status_code})
    if re.search(r'환불|파손|보증\s*청구',text):
        return say('주문 번호와 원결제 거래 해시를 알려 주세요. 장부에서 확인하겠습니다. 추가 송금은 하지 마세요.')
    items=[i for i in load(a.get('catalog_path','public/catalog.json'),{}).get('items',[]) if i.get('units') and i.get('stock',0)>0 and (not stamp(i.get('expires_at')) or stamp(i['expires_at'])>t)]
    rp=a.get('reservations_path','public/reservations.jsonl')
    rid=d.get('reservation_id') or (re.search(r'reservation_id\s*[:=]\s*([\w-]+)',text) or [None,None])[1]
    def reservations():
        return {str(x.get('reservation_id',x.get('id',''))):x for x in rows(rp)}
    reserved=None
    if rid:
        reserved=reservations().get(str(rid))
        if not reserved or reserved.get('state',reserved.get('status'))!='held' or stamp(reserved.get('expires_at'))<=t:
            return say('유효한 예약을 찾지 못했습니다. 예약 번호와 만료 시간을 확인해 주세요.')
    grade=d.get('grade') or (re.search(r'(?i)\b([abc])\s*(?:등급|급)',text) or [None,None])[1]
    sku=str((reserved or {}).get('sku') or d.get('sku') or '')
    if not sku:
        sm=re.search(r'\bG[0-9a-fA-F]{8}\b',text)
        if sm: sku=sm.group()
    q=words(text)
    def match(i):
        if sku: return i['sku'].lower()==sku.lower()
        iw=words(i['name']) | words(i.get('category',''))
        return any((set(ALIASES[w]) & iw) if w in ALIASES else w in iw for w in q)
    reserved_unit=(reserved or {}).get('unit') or (reserved or {}).get('unit_id')
    matching=[i for i in items if match(i) and (not reserved_unit or reserved_unit in i['units'])]
    candidates=sorted((i for i in matching if not grade or i['grade']==str(grade).upper()),key=lambda i:i['price'])
    if not candidates:
        showing=matching if matching else items
        lead='요청하신 등급은 없습니다. 보유 등급입니다.' if matching else '요청하신 상품을 확인하지 못했습니다. 현재 판매 목록입니다.'
        return say(lead+'\n'+('\n'.join('- '+info(i) for i in showing[:8]) if showing else '지금은 판매 가능한 재고가 없습니다.')+'\n원하시는 상품과 등급을 알려 주세요.')
    conditional=bool(re.search(r'있으면|가능하면|괜찮으면|맞으면|라면|다면|조건|검토|확인하고|부탁드립니다만|말고|동시에|두 가지|그리고|및|또한|도\s*(?:재고|있|함께)|배송|설치|묶음|세트',text))
    if len(re.findall(r'\bG[0-9a-fA-F]{8}\b',text))>1: conditional=True
    mentioned={w for w in q if w in ALIASES}
    mentioned={ '계란' if w=='달걀' else w for w in mentioned }
    if len(mentioned)>1: conditional=True
    try: qty=int(d.get('qty',1))
    except (ValueError,TypeError): qty=0
    if re.search(r'(?:[2-9]\d*|1\d+|두|세|네|여러)\s*(?:개|팩|병|봉|단위)(?!입)',text): qty=2
    intent=d.get('action') in ('checkout','buy') or bool(re.search(r'구매하겠습니다|살게요|구매합니다|주문하겠습니다|결제하겠습니다|결제할게요|구매\s*확정|주문\s*확정|결제서\s*(?:보내\s*주세요|주세요)|checkout(?:_jwt)?\s*(?:보내\s*주세요|주세요)',text,re.I))
    distinct={i['sku'] for i in candidates}
    if not reserved and (not intent or conditional or qty!=1 or len(distinct)!=1):
        return say('판매 가능 상품입니다.\n'+'\n'.join('- '+info(i) for i in candidates[:8])+'\n결제하려면 원하시는 상품 한 가지와 등급을 지정해 구매를 확정해 주세요.')
    inv=market(kit,'/api/inventory')
    inv.raise_for_status()
    live={u.get('unit'):u for u in fields(inv.json()) if u.get('unit')}
    hp=a.get('holds_path','holds.json')
    os.makedirs(os.path.dirname(hp) or '.',exist_ok=True)
    with open(hp,'a+',encoding='utf-8') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        f.seek(0); raw=f.read()
        holds=json.loads(raw) if raw.strip() else {}
        holds={k:v for k,v in holds.items() if isinstance(v,dict) and stamp(v.get('expires',v.get('expires_at')))>t}
        rs=reservations()
        if reserved and rs.get(str(rid))!=reserved:
            return say('예약 상태가 바뀌었습니다. 예약 번호를 확인해 주세요.')
        blocked={v.get('unit') or v.get('unit_id') for k,v in rs.items() if k!=str(rid) and v.get('state',v.get('status'))=='held' and stamp(v.get('expires_at'))>t}
        for i in candidates:
            for unit in sorted(i['units'],key=lambda u:(stamp(live.get(u,{}).get('supplied_at')) or float('inf'),u)):
                u=live.get(unit,{})
                if not unit or unit in blocked or u.get('sku')!=i['sku'] or u.get('grade')!=i['grade'] or (reserved and unit!=reserved_unit): continue
                exp=stamp(u.get('expires_at'))
                if exp and exp<=time.time(): continue
                cost=u.get('cost')
                price=(reserved or {}).get('unit_price',i['price'])
                if type(cost) is not int or cost<0 or type(price) is not int or price-price//100-210<cost: continue
                old=holds.get(unit)
                if old:
                    if a.get('context_id') and old.get('context_id')==a['context_id'] and old.get('task_id')==a.get('task_id') and old.get('payload',{}).get('price')==price and old.get('payload',{}).get('unit')==unit and old.get('reply_data',{}).get('checkout_jwt'):
                        return say(old['reply'],data=old['reply_data'])
                    continue
                wid=i.get('warranty_hours',0) or 0
                payload={'id':str(uuid.uuid4()),'shop':kit.name,'shop_url':kit.shop_url,'item':i['sku'],'price':price,'task':str(a.get('task_id') or uuid.uuid4()),'currency':'credits','iat':int(time.time()),'unit':unit,'warranty_hours':wid}
                if u.get('cert'): payload['cert']=u['cert']
                jwt=kit.sign_jwt(payload,'shop')
                reply=info(dict(i,price=price,expires_at=exp))+'입니다. 결제 후 order, checkout_mandate, payment_mandate(결제·수수료 거래 해시 포함)를 보내 주세요.'
                rd={'checkout_jwt':jwt,'sku':i['sku'],'grade':i['grade'],'price':price,'unit':unit}
                holds[unit]={'expires':time.time()+180,'context_id':a.get('context_id'),'task_id':a.get('task_id'),'payload':payload,'reply':reply,'reply_data':rd}
                f.seek(0); json.dump(holds,f,ensure_ascii=False); f.truncate(); f.flush()
                if reserved:
                    with open(rp,'a',encoding='utf-8') as rf: rf.write(json.dumps(dict(reserved,state='sold',status='sold',checkout_id=payload['id']),ensure_ascii=False)+'\n')
                return say(reply,data=rd)
    return say('현재 판매할 수 있는 실재고를 확인하지 못했습니다. 결제하지 마시고 다른 상품이나 등급을 선택해 주세요.')

def run(args,kit):
    d=args.get('data'); d=d if isinstance(d,dict) else {}
    t=time.time()
    try:
        ret=answer(args,kit,d,t)
    except Exception as e:
        ret={'ok':False,'error':type(e).__name__,'state':'input_required','reply':'지금 요청을 확인하지 못했습니다. 새로 결제하지 마시고, 이미 결제하셨다면 주문 번호와 기존 거래 해시를 보내 주세요.'}
    p=args.get('customers_path','customers.jsonl')
    os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
    out=ret.get('data',{})
    deal={k:out[k] for k in ('sku','grade','price','unit','settled') if k in out} if out.get('checkout_jwt') or out.get('settled') else None
    if out.get('checkout_jwt'): deal['checkout']=True
    with open(p,'a',encoding='utf-8') as f:
        f.write(json.dumps({'context_id':args.get('context_id'),'claimed_from':args.get('claimed_from'),'ts':t,'them':args.get('text',''),'you':ret['reply'],'deal':deal},ensure_ascii=False)+'\n')
    return ret
