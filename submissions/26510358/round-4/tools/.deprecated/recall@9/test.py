from pathlib import Path
import json
def test(run,kit):
 p=Path('tmp/test/customers');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'at':100,'text':'현미','reply':{'reply':'현미 없음','data':{'checkout_jwt':'secret'}}})+'\n'+json.dumps({'at':101,'text':'연결점검','reply':{}}),encoding='utf8')
 w=Path('tmp/test/wanted');w.write_text(json.dumps({'ts':100,'item':'현미','buyer':'a'}),encoding='utf8')
 r=run({'mode':'customer_summary','since':99,'now':102,'customer_path':str(p),'wanted_path':str(w)},kit);assert r['ok'] and len(r['messages'])==1 and r['messages'][0]['reply']=='현미 없음' and r['messages'][0]['checkout'] and r['wanted']==[('현미',1)] and 'secret' not in str(r)
 assert run({'word':''},kit)=={'matches':[],'count':0}
