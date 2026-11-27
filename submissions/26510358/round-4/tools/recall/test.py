from pathlib import Path
import json,uuid

def test(run,kit):
 p=Path('tmp/test')/uuid.uuid4().hex;p.mkdir(parents=True)
 (p/'customers').write_text(json.dumps({'ts':100,'text':'현미','reply':{'reply':'현미 B','data':{'checkouts':[1]}}})+'\n'+json.dumps({'ts':101,'text':'연결점검'}),encoding='utf8')
 (p/'wanted').write_text(json.dumps({'ts':100,'item':'현미'}),encoding='utf8')
 r=run({'mode':'customer_summary','since':99,'now':102,'customer_path':str(p/'customers'),'wanted_path':str(p/'wanted')},kit)
 assert r['ok'] and len(r['messages'])==1 and r['messages'][0]['checkout'] and r['wanted'][0][0]=='현미',r
 assert not run({'mode':'read','path':'../harness_check.json'},kit)['ok']
 assert run({'mode':'search','word':''},kit)['count']==0
