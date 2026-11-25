import json
from pathlib import Path

def run(args,kit):
    path=Path(args.get('card_path','card.json'))
    if kit.testing and (path.is_absolute() or path.parts[:2] != ('tmp','test') or '..' in path.parts or len(path.parts)<3):
        return {'ok':False,'error':'test card path must be under tmp/test/'}
    if not kit.testing and path != Path('card.json'):
        return {'ok':False,'error':'production card path must be card.json'}
    items=args.get('items',[])
    if not isinstance(items,list):
        return {'ok':False,'error':'items must be a list'}
    obj={'name':kit.name,'description':'헤르메스 상점입니다. 계란·김치·채소·요거트·쌀 등 현재 재고를 판매합니다. 상품명 또는 SKU로 문의하시면 현재 등급·가격·유통기한·보증을 확인해 드립니다.','url':kit.shop_url,'roles':['shop'],'products':items,'buying':args.get('buying','상품명이나 SKU를 보내 주세요. 예약이 있으면 예약 ID도 알려 주세요.'),'language':'ko'}
    try:
        if kit.testing:
            path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
    except OSError as e:
        return {'ok':False,'error':str(e)}
    return {'written':True,'items':len(items)}
