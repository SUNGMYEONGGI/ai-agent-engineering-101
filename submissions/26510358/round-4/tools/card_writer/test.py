import json
from pathlib import Path

def test(run,kit):
 root=Path('tmp/test/card_writer');root.mkdir(parents=True,exist_ok=True)
 cat=root/'catalog.json';out=root/'card.json';st=root/'state.json'
 if st.exists():st.unlink()
 cat.write_text(json.dumps({'items':[{'sku':'egg','name':'계란 20구','grade':'B','price':7900,'stock':2,'units':['u1','sold'],'warranty_hours':0},{'sku':'tofu','name':'두부 300g','grade':'C','price':2000,'stock':1,'units':['u2'],'warranty_hours':0},{'sku':'high','name':'비싼 쌀','grade':'B','price':5000,'stock':1,'units':['u3']}]},ensure_ascii=False),encoding='utf8')
 a={'catalog_path':str(cat),'card_path':str(out),'forum_state_path':str(st),'now':10000,'ledger_fixture':[{'kind':'settle','data':{'sku':'egg','grade':'B','amount':8000}},{'kind':'settle','data':{'sku':'tofu','grade':'C','amount':2100}},{'kind':'settle','data':{'sku':'high','grade':'B','amount':4000}}],'inventory_fixture':{'units':[{'unit':'u1','sku':'egg','grade':'B','expires_at':20000},{'unit':'u2','sku':'tofu','grade':'C','expires_at':20000},{'unit':'u3','sku':'high','grade':'B','expires_at':20000}]},'forum_fixture':[]}
 r=run(a,kit);assert r['ok'] and r['forum']=='posted',r
 assert '계란 20구 B등급 7900' in r['text'] and '시장 중간가 8000' in r['text'] and '비싼 쌀' not in r['text']
 card=json.loads(out.read_text(encoding='utf8'));assert len(card['skills'])==4 and card['products'][0]['stock']==1
 assert all(all(k in s for k in ('id','name','description','tags','examples')) for s in card['skills'])
 a['now']=10599;assert run(a,kit)['forum']=='skipped: cooldown'
 a['now']=10600;r2=run(a,kit);assert r2['forum']=='posted' and r2['text']!=r['text'],r2
 return True
