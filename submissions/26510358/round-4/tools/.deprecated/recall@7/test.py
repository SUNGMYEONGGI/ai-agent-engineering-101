from pathlib import Path
def test(run,kit):
 p=Path('tmp/test/rcsrc');p.parent.mkdir(parents=True,exist_ok=True);p.write_text('hello');r=run({'mode':'backup_current','source':str(p),'dest':'tmp/test/rcdest'},kit);assert r['ok'] and Path('tmp/test/rcdest').read_text()=='hello';assert run({'word':''},kit)=={'matches':[],'count':0}