import json
from pathlib import Path

def test(run,kit):
    production=Path('card.json')
    before=production.read_bytes() if production.exists() else None
    assert run({},kit)['ok'] is False
    assert run({'card_path':'tmp/test/../../card.json'},kit)['ok'] is False
    sample={'sku':'Gtest','name':'계란','grade':'A','price':9120,'stock':1,'warranty_hours':0,'expires_at':1795898496}
    path=Path('tmp/test/agent-card-sample.json')
    res=run({'card_path':str(path),'items':[sample],'buying':'상품명으로 문의해 주세요.'},kit)
    assert res=={'written':True,'items':1}
    card=json.loads(path.read_text(encoding='utf8'))
    assert all(card.get(k) for k in ('name','description','url','roles','products','buying','language'))
    assert card['language']=='ko' and card['roles']==['shop'] and card['url']==kit.shop_url
    assert card['products']==[sample]
    assert (production.read_bytes() if production.exists() else None)==before
