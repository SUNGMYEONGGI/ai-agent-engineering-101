from pathlib import Path
import json,time
src=Path('ops/a2a_v16.py').read_text(encoding='utf8')
old="   result['reply']=reply"
new="   reply=fruit_notice(text,reply,a,kit)\n   if checks: reply=wallet_reply(reply,checks,kit)\n   result['reply']=reply"
assert old in src
src=src.replace(old,new,1)
def wallet_reply(reply,checks,kit):
 if checks:return reply+'\n가게 지갑 주소: '+str(kit.address('shop'))+'. 결제서와 결제 안내를 확인해 주세요.'
 return reply
def fruit_notice(text,reply,a,kit):
 if '과일' in text and '과일' not in reply:
  reply+='\n요청하신 소량 과일의 포장량·등급·소비기한 조건에 맞는 상품은 아직 확인하지 못했습니다.'
  wp=b['checked_path'](a,'wanted_path','wanted.jsonl',kit.testing);wp.parent.mkdir(parents=True,exist_ok=True)
  with wp.open('a',encoding='utf8') as f:f.write(json.dumps({'ts':int(time.time()),'item':'과일','buyer':a.get('claimed_from')},ensure_ascii=False)+'\n')
 return reply
exec(compile(src,'ops/a2a_v16.py','exec'),globals())
original_run=run
def run(args,kit):return original_run(args,kit)