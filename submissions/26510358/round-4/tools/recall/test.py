from pathlib import Path
def test(run,kit):
 p=Path('tmp/test/rsource');p.parent.mkdir(parents=True,exist_ok=True);p.write_text('test');assert run({'mode':'restore','source':str(p),'dest':'tmp/test/rdest'},kit)['ok'];assert Path('tmp/test/rdest').read_text()=='test';assert run({'word':''},kit)=={'matches':[],'count':0}