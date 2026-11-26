from pathlib import Path
src=Path('ops/a2a_v16.py').read_text(encoding='utf8')
old="   result['reply']=reply"
new="   if checks: reply=wallet_reply(reply,checks,kit)\n   result['reply']=reply"
assert old in src
src=src.replace(old,new,1)
def wallet_reply(reply,checks,kit):
 if checks:return reply+'\n가게 지갑 주소: '+str(kit.address('shop'))+'. 결제서와 결제 안내를 확인해 주세요.'
 return reply
exec(compile(src,'ops/a2a_v16.py','exec'),globals())
original_run=run
def run(args,kit):return original_run(args,kit)