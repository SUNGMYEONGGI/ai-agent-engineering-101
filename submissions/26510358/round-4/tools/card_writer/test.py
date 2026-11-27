import json
from pathlib import Path

def test(run,kit):
 p=Path('tmp/test/cardwriter9');p.mkdir(parents=True,exist_ok=True)
 cat=p/'catalog.json';out=p/'card.json';state=p/'state.json'
 if state.exists():state.unlink()
 items=[{'sku':'e','name':'한계란 난각번호 1번 유정란 20구','grade':'B','price':100,'stock':1,'units':['u1'],'warranty_hours':0},{'sku':'w','name':'[본사공식] 몽베스트 무라벨 생수 2Lx6병','grade':'C','price':300,'stock':1,'units':['u2'],'warranty_hours':0},{'sku':'bad','name':'비싼 두부','grade':'B','price':999,'stock':1,'units':['u3'],'warranty_hours':0}]
 cat.write_text(json.dumps({'items':items},ensure_ascii=False),encoding='utf8')
 inv={'units':[{'unit':'u1','sku':'e','grade':'B','expires_at':2000},{'unit':'u2','sku':'w','grade':'C','expires_at':2000},{'unit':'u3','sku':'bad','grade':'B','expires_at':2000}]}
 ledger=[{'kind':'settle','round':4,'data':{'sku':'e','grade':'B','amount':110}},{'kind':'settle','round':4,'data':{'sku':'w','grade':'C','amount':300}},{'kind':'settle','round':4,'data':{'sku':'bad','grade':'B','amount':400}}]
 args={'catalog_path':str(cat),'card_path':str(out),'forum_state_path':str(state),'now':1000,'inventory_fixture':inv,'ledger_fixture':ledger,'forum_fixture':[]}
 r=run(args,kit);assert r['ok'] and r['forum']=='posted';card=json.loads(out.read_text(encoding='utf8'));assert '계란 20구' in card['description'] and '생수' in card['description'] and '[본사공식]' not in card['description'] and '두부' not in card['description'];assert len(card['products'])==3 and all({'id','name','description','tags','examples'}<=set(s) for s in card['skills']);assert '시장 중간가' in r['text'] and '비싼 두부' not in r['text'];assert run(args,kit)['forum']=='skipped: cooldown'
 args['now']=1601;assert run(args,kit)['forum']=='posted'
