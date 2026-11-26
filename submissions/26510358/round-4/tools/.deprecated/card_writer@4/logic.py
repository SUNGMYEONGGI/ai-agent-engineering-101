import json
import uuid
from pathlib import Path
from urllib.parse import urlsplit
import httpx

HOST='rome-edt-vendors-august.trycloudflare.com'
CARD='https://'+HOST+'/.well-known/agent-card.json'
KEYWORDS=('계란','김치','채소','콩나물','취나물','시금치','요거트','쌀','생수','둥굴레차','두부','고구마','고등어','키친타올')

def safe_endpoint(url):
    if not isinstance(url,str): return False
    u=urlsplit(url)
    return u.scheme=='https' and u.netloc==HOST and not u.fragment and not u.query and u.path.rstrip('/')!='/.well-known/agent-card.json'

def probe(args,kit):
    stage='card'
    try:
        fake=args.get('probe_fixture',{}) if kit.testing else None
        r=httpx.get(CARD,headers={'cache-control':'no-cache'},timeout=8,follow_redirects=False) if fake is None else None
        if r is not None: r.raise_for_status()
        card=r.json() if r is not None else fake['card']
        if not isinstance(card,dict) or not card.get('name') or not isinstance(card.get('skills'),list):
            return {'ok':False,'error':'공개 카드 형식 오류','stage':stage}
        endpoint=card.get('url')
        if not safe_endpoint(endpoint): return {'ok':False,'error':'카드에 안전한 상점 A2A 주소 없음','stage':stage}
        stage='a2a'
        rid=str(uuid.uuid4())
        payload={'jsonrpc':'2.0','id':rid,'method':'message/send','params':{'message':{'kind':'message','role':'user','messageId':rid,'parts':[{'kind':'text','text':'안녕하세요. 연결점검입니다.'}]}}}
        res=httpx.post(endpoint,json=payload,timeout=14,follow_redirects=False) if fake is None else None
        status=res.status_code if res is not None else fake.get('status',200)
        products=card.get('products',[])
        summary={'products':len(products) if isinstance(products,list) else 0,'skills':len(card['skills']),'endpoint':endpoint,'a2a_status':status}
        if status!=200: return {'ok':False,'error':'A2A HTTP '+str(status),**summary}
        reply=res.json() if res is not None else fake['response']
        if not isinstance(reply,dict): return {'ok':False,'error':'A2A 응답 객체 없음',**summary}
        if reply.get('error') is not None:
            err=reply['error']; return {'ok':False,'error':'A2A JSON-RPC 오류','rpc_code':err.get('code') if isinstance(err,dict) else None,**summary}
        if reply.get('jsonrpc')!='2.0' or (fake is None and reply.get('id')!=rid) or not isinstance(reply.get('result'),dict):
            return {'ok':False,'error':'A2A JSON-RPC 결과 형식 오류',**summary}
        result=reply['result']; s=result.get('status') or {}; s=s if isinstance(s,dict) else {}
        out=[]
        def walk(node,depth=0):
            if depth>6: return
            if isinstance(node,list):
                for x in node[:12]: walk(x,depth+1)
            elif isinstance(node,dict):
                if isinstance(node.get('text'),str) and node.get('kind',node.get('type'))=='text': out.append(node['text'])
                for k in ('parts','message','history','artifacts'): walk(node.get(k),depth+1)
        walk(result.get('parts')); walk(s.get('message')); walk(result.get('artifacts'))
        if not out: return {'ok':False,'error':'A2A 응답 텍스트 없음','state':s.get('state'),**summary}
        result={'ok':True,**summary,'state':s.get('state'),'reply_text':'\n'.join(out)[:550]}
        if kit.testing: result['request']=payload
        return result
    except httpx.HTTPStatusError as e: return {'ok':False,'error':'HTTP '+str(e.response.status_code),'stage':stage}
    except (httpx.HTTPError,ValueError,KeyError,TypeError) as e: return {'ok':False,'error':type(e).__name__,'stage':stage}

def test_path(path):
    return not path.is_absolute() and path.parts[:2]==('tmp','test') and len(path.parts)>2 and '..' not in path.parts and path.resolve().is_relative_to(Path('tmp/test').absolute())

def run(args,kit):
    if args.get('mode')=='probe': return probe(args,kit)
    try:
        path=Path(args.get('card_path','card.json'))
        if kit.testing and not test_path(path): return {'ok':False,'error':'test card path must be under tmp/test/'}
        if not kit.testing and path!=Path('card.json'): return {'ok':False,'error':'production card path must be card.json'}
        if 'items' in args: items=args['items']
        else:
            catalog=Path(args.get('catalog_path','public/catalog.json'))
            if (kit.testing and not test_path(catalog)) or (not kit.testing and catalog!=Path('public/catalog.json')): return {'ok':False,'error':'invalid catalog path'}
            items=json.loads(catalog.read_text(encoding='utf8'))['items']
        if not isinstance(items,list) or any(not isinstance(x,dict) for x in items): return {'ok':False,'error':'items must be a list of objects'}
        products=[{k:x[k] for k in ('sku','name','grade','price','stock','warranty_hours','expires_at') if k in x} for x in items if type(x.get('stock')) is int and x['stock']>0 and all(x.get(k) for k in ('sku','name','grade','price'))]
        names=list(dict.fromkeys(x['name'] for x in products if isinstance(x['name'],str)))
        tags=['장보기','상품 검색','재고 확인','구매']+[word for word in KEYWORDS if any(word in n for n in names)]
        buying=args.get('buying','상품명이나 SKU를 보내 주세요. 예약이 있으면 예약 ID도 알려 주세요. 결제 전 상품 등급·가격·유통기한·보증 여부를 확인해 주세요.')
        skill={'id':'shop-purchase','name':'헤르메스 상점 상품 검색 및 구매','description':buying,'tags':tags,'examples':[f'{n} 재고와 가격을 알려 주세요.' for n in names[:8]] or ['지금 구매할 수 있는 상품을 알려 주세요.']}
        obj={'name':kit.name,'description':'헤르메스 상점입니다. 상품 이름 일부만 알려 주셔도 구매 가능한 재고의 등급·가격·유통기한·보증 여부를 안내합니다.','url':kit.shop_url,'roles':['shop'],'products':products,'skills':[skill],'buying':buying,'language':'ko'}
        if kit.testing: path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
        return {'ok':True,'written':True,'items':len(products),'skills':1}
    except (OSError,ValueError,KeyError,TypeError) as e: return {'ok':False,'error':str(e)}