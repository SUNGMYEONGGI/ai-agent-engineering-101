from pathlib import Path
def test(run,kit):
 p=Path('tmp/test/recall_src');p.parent.mkdir(parents=True,exist_ok=True);p.write_text('hello');r=run({'mode':'backup','source':str(p),'dest':'tmp/test/recall_dest'},kit);assert r['ok'] and Path('tmp/test/recall_dest').read_text()=='hello'
 assert run({'word':''},kit)=={'matches':[],'count':0}
