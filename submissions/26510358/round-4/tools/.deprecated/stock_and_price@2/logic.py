import json, os

def run(args, kit):
    items=args.get('items') or []
    floor=args.get('floor')
    if floor is None: floor=0
    try: floor=int(floor)
    except: floor=0
    out=[]
    for x in items:
        y=dict(x)
        try: price=int(y.get('price') or 0)
        except: price=0
        try: stock=int(y.get('stock') or 0)
        except: stock=0
        y['price']=max(price,floor)
        y['stock']=max(0,stock)
        out.append(y)
    os.makedirs('public',exist_ok=True)
    with open('public/catalog.json','w',encoding='utf-8') as f:
        json.dump({'items':out},f,ensure_ascii=False,separators=(',',':'))
    return {'items':out,'count':len(out)}
