from pathlib import Path
import json,re,time,urllib.request

def _path(a,k,d): return Path(a.get(k,d))
def _inv(a,kit):
    if isinstance(a.get('inventory_fixture'),dict): return a['inventory_fixture'].get('units',[])
    q=urllib.request.Request(kit.market+'/api/inventory',headers={'authorization':'Bearer '+kit.token('shop')})
    with urllib.request.urlopen(q,timeout=12) as r: return json.loads(r.read()).get('units',[])
def _wanted(a,item):
    p=_path(a,'wanted_path','wanted.jsonl');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a',encoding='utf8') as f:f.write(json.dumps({'ts':time.time(),'item':item,'buyer':a.get('claimed_from')},ensure_ascii=False)+'\\n')
def run(a,kit):
    text=str(a.get('text') or '')
    try: units=_inv(a,kit)
    except Exception: return {'reply':'현재 재고를 확인하지 못했습니다. 잠시 후 다시 문의해 주세요.','state':'input_required'}
    hp=_path(a,'holds_path','holds.json'); held=set()
    if hp.exists():
        try:
            z=json.loads(hp.read_text());held=set(z if isinstance(z,list) else z.keys())
        except Exception: pass
    names=[str(u.get('name',u.get('product_name',u.get('sku','')))) for u in units]
    known=['계란','유정란','시금치','두부','취나물','우유','김치','백미','현미','쌀','커피','차','총각김치']
    requested=[k for k in known if k in text]
    matched=[]
    for u in units:
        uid=str(u.get('unit_id',u.get('id',u.get('unit','')))); n=str(u.get('name',u.get('product_name',u.get('sku',''))))
        if uid in held or str(u.get('status','')).lower() in ('sold','held','expired') or u.get('sold') or u.get('expired'): continue
        if any(k in n for k in requested): matched.append(u)
    chosen=[];seen=set()
    for u in matched:
        key=str(u.get('sku',u.get('name',u.get('product_name',''))))
        if key not in seen:chosen.append(u);seen.add(key)
    missing=[k for k in requested if not any(k in str(u.get('name',u.get('product_name',''))) for u in chosen)]
    for k in missing:_wanted(a,k)
    if not chosen:
        avail=[]
        for u in units:
            n=str(u.get('name',u.get('product_name',u.get('sku',''))))
            if n and n not in avail:avail.append(n)
        msg='요청하신 상품은 현재 보유 재고에서 확인되지 않습니다.'
        if avail:msg+=' 현재 구매 가능한 상품: '+' · '.join(avail[:5])+'.'
        return {'reply':msg,'state':'input_required'}
    lines=[];checks=[]
    for u in chosen:
        n=str(u.get('name',u.get('product_name',u.get('sku',''))));g=str(u.get('grade',''));p=int(u.get('price',u.get('list_price',0)));uid=str(u.get('unit_id',u.get('id',u.get('unit',''))))
        lines.append(f'{n} {g}등급 {p}크레딧');checks.append({'unit_id':uid,'item':n,'grade':g,'price':p})
    msg='확인한 실재고 기준입니다. '+'; '.join(lines)+'.'
    if any(u.get('cert_grade') is None for u in chosen) or 'cert' in text:msg+=' 인증서에는 등급이 기재되지 않으며 상품 등급은 현재 재고 표기 기준입니다.'
    if missing:msg+=' 현재 '+', '.join(missing)+'은(는) 보유 재고에서 확인되지 않습니다.'
    return {'reply':msg,'data':{'checkouts':checks},'state':'completed'}
