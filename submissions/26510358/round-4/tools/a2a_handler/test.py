from pathlib import Path
def test(run,kit):
 ns={};exec(compile(Path('ops/a2a_v16_test.py').read_text(encoding='utf8'),'ops/a2a_v16_test.py','exec'),ns);ns['test'](run,kit)
 f=run.__globals__['wallet_reply'];addr=str(kit.address('shop'));assert addr in f('결제서',[{'sku':'x'}],kit);assert f('없음',[],kit)=='없음'