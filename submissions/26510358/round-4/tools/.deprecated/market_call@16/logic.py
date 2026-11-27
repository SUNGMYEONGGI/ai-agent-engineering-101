from pathlib import Path
p=Path('tools/.deprecated/market_call@14/logic.py')
if not p.exists():p=Path('tools/market_call/logic.py')
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),globals())
_old_run=run
def full_ledger(fetch):
 allrows=[];cursor=-5000
 for i in range(20):
  page=rows(fetch(cursor))
  if not page:break
  allrows.extend(page)
  seqs=[x.get('seq') for x in page if isinstance(x,dict) and isinstance(x.get('seq'),int)]
  if not seqs:break
  nxt=max(seqs)
  if cursor>=0 and nxt<=cursor:break
  cursor=nxt
 return allrows
def run(a,kit):
 if a.get('mode')!='metrics_full':return _old_run(a,kit)
 try:
  if kit.testing:
   pages=a.get('pages_fixture'); l=full_ledger(lambda c:pages.get(str(c),[])) if pages is not None else a['ledger_fixture']
  else:l=full_ledger(lambda c:req(kit,'/api/ledger?after='+str(c)))
  logs=a.get('logs_fixture',[]) if kit.testing else getlogs(a.get('logs_path','customers.jsonl'))
  out=metrics(l,logs,a.get('now',time.time()),kit)
  return {'ok':True,**out,'last_seq':max((x.get('seq',0) for x in l if isinstance(x,dict)),default=0)}
 except Exception as e:return {'ok':False,'error':str(e)}