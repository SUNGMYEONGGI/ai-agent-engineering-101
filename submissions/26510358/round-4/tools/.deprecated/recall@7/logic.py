from pathlib import Path

def run(a,kit):
 try:
  mode=a.get('mode')
  if mode=='backup_current':
   if kit.testing:
    src=Path(a['source']);dest=Path(a['dest']);assert src.parts[:2]==('tmp','test') and dest.parts[:2]==('tmp','test');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(src.read_text(encoding='utf8'),encoding='utf8');return {'ok':True}
   for s,d in [('tools/a2a_handler/logic.py','ops/a2a_v16.py'),('tools/a2a_handler/test.py','ops/a2a_v16_test.py')]:
    p=Path(d);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(Path(s).read_text(encoding='utf8'),encoding='utf8')
   return {'ok':True}
  if mode=='backup':
   src=Path(a.get('source','tools/a2a_handler/logic.py'));dest=Path(a.get('dest','ops/a2a_v11.py'))
   if kit.testing:
    assert src.parts[:2]==('tmp','test') and dest.parts[:2]==('tmp','test')
   elif str(src)!='tools/a2a_handler/logic.py' or str(dest)!='ops/a2a_v11.py':raise ValueError('invalid path')
   dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(src.read_text(encoding='utf8'),encoding='utf8');return {'ok':True,'bytes':dest.stat().st_size}
  w=str(a.get('word','')).lower();out=[]
  if not w:return {'matches':[],'count':0}
  for p in a.get('paths',['logs/react.jsonl','logs/agent-kit.log']):
   try:
    with open(p,encoding='utf8') as f:
     for line in f:
      if w in line.lower():out.append({'file':p,'line':line.rstrip()})
   except (OSError,UnicodeError):pass
  return {'matches':out[-50:],'count':len(out)}
 except Exception as e:return {'ok':False,'error':str(e)}