import json
from pathlib import Path

def test_path(path):
    return not path.is_absolute() and path.parts[:2] == ('tmp','test') and len(path.parts)>2 and '..' not in path.parts and path.resolve().is_relative_to(Path('tmp/test').absolute())

def run(args,kit):
    try:
        path=Path(args.get('card_path','card.json'))
        if kit.testing and not test_path(path):
            return {'ok':False,'error':'test card path must be under tmp/test/'}
        if not kit.testing and path != Path('card.json'):
            return {'ok':False,'error':'production card path must be card.json'}
        if 'items' in args:
            items=args['items']
        else:
            catalog=Path(args.get('catalog_path','public/catalog.json'))
            if (kit.testing and not test_path(catalog)) or (not kit.testing and catalog!=Path('public/catalog.json')):
                return {'ok':False,'error':'invalid catalog path'}
            items=json.loads(catalog.read_text(encoding='utf8'))['items']
        if not isinstance(items,list) or any(not isinstance(x,dict) for x in items):
            return {'ok':False,'error':'items must be a list of objects'}
        products=[{k:x[k] for k in ('sku','name','grade','price','stock','warranty_hours','expires_at') if k in x} for x in items if type(x.get('stock')) is int and x['stock']>0 and all(x.get(k) for k in ('sku','name','grade','price'))]
        keywords=('계란','김치','채소','콩나물','취나물','시금치','요거트','쌀','생수','둥굴레차','두부','고구마','고등어','키친타올')
        names=list(dict.fromkeys(x['name'] for x in products if isinstance(x['name'],str)))
        tags=['장보기','상품 검색','재고 확인','구매']+[word for word in keywords if any(word in n for n in names)]
        buying=args.get('buying','상품명이나 SKU를 보내 주세요. 예약이 있으면 예약 ID도 알려 주세요. 결제 전 상품 등급·가격·유통기한·보증 여부를 확인해 주세요.')
        skill={'id':'shop-purchase','name':'헤르메스 상점 상품 검색 및 구매','description':buying,'tags':tags,'examples':[f'{name} 재고와 가격을 알려 주세요.' for name in names[:8]] or ['지금 구매할 수 있는 상품을 알려 주세요.']}
        obj={'name':kit.name,'description':'헤르메스 상점입니다. 상품 이름 일부만 알려 주셔도 구매 가능한 재고의 등급·가격·유통기한·보증 여부를 안내합니다.','url':kit.shop_url,'roles':['shop'],'products':products,'skills':[skill],'buying':buying,'language':'ko'}
        if kit.testing:
            path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
        return {'ok':True,'written':True,'items':len(products),'skills':1}
    except (OSError,ValueError,KeyError,TypeError) as e:
        return {'ok':False,'error':str(e)}
