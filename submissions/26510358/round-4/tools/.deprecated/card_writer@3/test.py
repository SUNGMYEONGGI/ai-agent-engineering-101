import json
from pathlib import Path

def test(run,kit):
    production=Path('card.json')
    before=production.read_bytes() if production.exists() else None
    assert run({},kit)['ok'] is False
    assert run({'card_path':'tmp/test/../../card.json','items':[]},kit)['ok'] is False
    base=Path('tmp/test')
    base.mkdir(parents=True,exist_ok=True)
    path=base/'card_skill_sample.json'
    catalog=base/'card_catalog_sample.json'
    sample={'sku':'Gtest','name':'계란','grade':'A','price':9120,'stock':1,'units':['test-unit'],'warranty_hours':0,'expires_at':1795898496}
    catalog.write_text(json.dumps({'items':[sample,dict(sample,sku='Gempty',name='김치',stock=0)]}),encoding='utf8')
    assert not run({'card_path':str(path)},kit)['ok']
    res=run({'card_path':str(path),'catalog_path':str(catalog)},kit)
    assert res=={'ok':True,'written':True,'items':1,'skills':1}
    card=json.loads(path.read_text(encoding='utf8'))
    assert all(card.get(k) for k in ('name','description','url','roles','products','buying','language','skills'))
    assert card['language']=='ko' and card['roles']==['shop'] and card['url']==kit.shop_url
    assert card['products']==[{k:v for k,v in sample.items() if k!='units'}]
    skill=card['skills'][0]
    assert all(skill.get(k) for k in ('id','name','description','tags','examples'))
    assert '계란' in skill['tags'] and '김치' not in skill['tags'] and '계란' in skill['examples'][0]
    assert (production.read_bytes() if production.exists() else None)==before
