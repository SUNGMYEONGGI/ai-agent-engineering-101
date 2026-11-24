import json

def run(args,kit):
    items=args.get('items',[])
    obj={'name':kit.name,'description':'헤르메스 상점입니다. 재고의 현재 등급과 가격을 공개하고 예약 후 checkout_jwt 결제로 판매합니다. 품질·유통기한·보증은 상품별 catalog에 표시된 사실만 안내합니다.','url':kit.shop_url,'roles':['shop'],'products':items,'buying':args.get('buying','상품 SKU와 예약 ID를 문의해 주세요. 결제 전 가격·등급·재고를 확인합니다.'),'language':'ko'}
    with open('card.json','w',encoding='utf8') as f: json.dump(obj,f,ensure_ascii=False,indent=2)
    return {'written':True,'items':len(items)}
