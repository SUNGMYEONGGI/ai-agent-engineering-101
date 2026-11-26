import json
from pathlib import Path

def test(run,kit):
    p=Path('card.json'); before=p.read_bytes() if p.exists() else None
    assert run({},kit)['ok'] is False
    assert run({'card_path':'tmp/test/../../card.json','items':[]},kit)['ok'] is False
    base=Path('tmp/test'); base.mkdir(parents=True,exist_ok=True)
    path=base/'card_skill_sample.json'; catalog=base/'card_catalog_sample.json'
    sample={'sku':'Gtest','name':'계란','grade':'A','price':9120,'stock':1,'units':['test-unit'],'warranty_hours':0,'expires_at':1795898496}
    catalog.write_text(json.dumps({'items':[sample,dict(sample,sku='Gempty',name='김치',stock=0)]}),encoding='utf8')
    assert not run({'card_path':str(path)},kit)['ok']
    assert run({'card_path':str(path),'catalog_path':str(catalog)},kit)=={'ok':True,'written':True,'items':1,'skills':1}
    card=json.loads(path.read_text(encoding='utf8'))
    assert all(card.get(k) for k in ('name','description','url','roles','products','buying','language','skills'))
    assert card['url']==kit.shop_url and card['roles']==['shop'] and card['language']=='ko'
    assert card['products']==[{k:v for k,v in sample.items() if k!='units'}]
    skill=card['skills'][0]; assert all(skill.get(k) for k in ('id','name','description','tags','examples'))
    assert '계란' in skill['tags'] and '김치' not in skill['tags'] and '계란' in skill['examples'][0]
    card['url']='https://rome-edt-vendors-august.trycloudflare.com/'
    response={'jsonrpc':'2.0','id':'sample','result':{'kind':'task','status':{'state':'input-required','message':{'kind':'message','role':'agent','messageId':'sample-reply','parts':[{'kind':'text','text':'계란 A등급 9120 credits'}]}}}}
    def invoke(**overrides): return run({'mode':'probe','probe_fixture':{'card':card,'response':response,**overrides}},kit)
    r=invoke(); assert r['ok'] and r['reply_text']=='계란 A등급 9120 credits'
    q=r['request']; assert all(q.get(k) for k in ('jsonrpc','id','method','params')) and q['method']=='message/send'
    m=q['params']['message']; assert all(m.get(k) for k in ('kind','role','messageId','parts')) and m['role']=='user'
    assert m['parts']==[{'kind':'text','text':'안녕하세요. 연결점검입니다.'}]
    assert not invoke(status=502)['ok']
    assert not invoke(response={'jsonrpc':'2.0','error':{'code':-32601}})['ok']
    assert not invoke(card=dict(card,url='https://other.example/'))['ok']
    assert (p.read_bytes() if p.exists() else None)==before