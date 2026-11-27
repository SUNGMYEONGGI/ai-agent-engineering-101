from pathlib import Path
p=Path('tools/.deprecated/market_call@14/logic.py')
if not p.exists():p=Path('tools/market_call/logic.py')
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),globals())
_old_run=run
def run(a,kit):
 if a.get('mode')!='metrics_full':return _old_run(a,kit)
 try:
  l=a['ledger_fixture'] if kit.testing else req(kit,'/api/ledger?after=-5000')
  logs=a.get('logs_fixture',[]) if kit.testing else getlogs(a.get('logs_path','customers.jsonl'))
  out=metrics(l,logs,a.get('now',time.time()),kit)
  return {'ok':True,**out}
 except Exception as e:return {'ok':False,'error':str(e)}