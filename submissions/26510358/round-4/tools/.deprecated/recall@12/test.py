from pathlib import Path
import json,uuid

def test(run,kit):
 root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True);p=root/uuid.uuid4().hex;p.mkdir()
 (p/'customers').write_text(json.dumps({'ts':100,'text':'현미','reply':{'reply':'없음','data':{'checkouts':[1]}}})+'\n'+json.dumps({'ts':101,'text':'연결점검'}),encoding='utf8');(p/'wanted').write_text(json.dumps({'ts':100,'item':'현미'}),encoding='utf8')
 r=run({'mode':'customer_summary','since':99,'now':102,'customer_path':str(p/'customers'),'wanted_path':str(p/'wanted')},kit);assert r['ok'] and len(r['messages'])==1 and r['wanted'][0][0]=='현미'
 r=run({'mode':'stage_test','logic':'def run(a,kit): return 42','test':'def test(run,kit): assert run({},kit)==42'},kit);assert r['ok'],r
 assert run({'mode':'read','path':'../harness_check.json'},kit)['ok']==False
 assert run({'word':''},kit)=={'matches':[],'count':0}