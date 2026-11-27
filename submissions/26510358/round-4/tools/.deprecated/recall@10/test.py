from pathlib import Path
import json

def test(run,kit):
 p=Path('tmp/test/recallcustomers');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'ts':100,'text':'현미','reply':{'reply':'없음','data':{'checkouts':[1]}}})+'\n'+json.dumps({'ts':101,'text':'연결점검'}),encoding='utf8');w=Path('tmp/test/recallwanted');w.write_text(json.dumps({'ts':100,'item':'현미'}),encoding='utf8');r=run({'mode':'customer_summary','since':99,'now':102,'customer_path':str(p),'wanted_path':str(w)},kit);assert r['ok'] and len(r['messages'])==1 and r['messages'][0]['checkout'] and r['wanted'][0][0]=='현미';assert run({'word':''},kit)=={'matches':[],'count':0}
