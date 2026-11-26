from pathlib import Path
import json,time,re
src=Path('ops/a2a_v16.py').read_text(encoding='utf8')
base="src=Path('ops/a2a_v11.py').read_text(encoding='utf8')"
patch="src=src.replace(\"'warranty_hours':x.get('warranty_hours',0)}\",\"'warranty_hours':x.get('warranty_hours',0),'grade':u.get('grade')}\")"
assert base in src
src=src.replace(base,base+'\n'+patch,1)
src=src.replace("b['ORDER']=sorted(b['NOUNS'],key=len,reverse=True)","b['NOUNS'].update({'사료':['사료'], '배변패드':['배변패드'], '생선':['생선','고등어'], '과일':['과일','사과'], '빵':['빵'], '세탁세제':['세탁세제','세탁 보조용품'], '닭고기':['닭고기','닭가슴살','닭다리'], '달걀 30구':['계란 30구','달걀 30구','계란30구','달걀30구'], '계란 30구':['계란 30구','달걀 30구','계란30구','달걀30구'], '믹스커피':['믹스커피','믹스 커피'], '믹스 커피':['믹스커피','믹스 커피'], '유정란':['유정란']})\nb['ORDER']=sorted(b['NOUNS'],key=len,reverse=True)")
src=src.replace('/api/ledger?after=-500','/api/ledger?after=-2000')
src=src.replace("h.get('expires_at',0) if isinstance(h,dict) else h","h.get('expires_at',h.get('until',0)) if isinstance(h,dict) else h")
old="   result['reply']=reply"
new="   reply=missing_notice(text,reply,a,kit)\n   if checks: reply=wallet_reply(reply,checks,kit)\n   result['reply']=reply"
assert old in src
src=src.replace(old,new,1)
def wallet_reply(reply,checks,kit):
 return reply+'\n가게 지갑 주소: '+str(kit.address('shop'))+'. 결제서와 결제 안내를 확인해 주세요.' if checks else reply
def missing_notice(text,reply,a,kit):
 missing=[x for x in ('과일','배추김치','사료','배변패드','생선','빵','세탁세제','닭고기') if (x in text or x=='세탁세제' and '세탁 보조용품' in text) and x not in reply]
 data=a.get('data') if isinstance(a.get('data'),dict) else {}
 match=re.search(r'\bG[0-9a-fA-F]{8}\b',text)
 sku=str(data.get('sku') or (match.group() if match else ''))
 if sku and re.search(r'SKU\s+'+re.escape(sku)+r'.{0,30}없습니다',reply,re.I):missing.append('SKU '+sku)
 if missing:
  notice=[x for x in missing if not x.startswith('SKU ')]
  if notice:reply+='\n요청하신 '+', '.join(notice)+'의 조건에 맞는 재고는 확인하지 못했습니다.'
  wp=b['checked_path'](a,'wanted_path','wanted.jsonl',kit.testing);wp.parent.mkdir(parents=True,exist_ok=True)
  with wp.open('a',encoding='utf8') as f:
   for x in missing:f.write(json.dumps({'ts':int(time.time()),'item':x,'buyer':a.get('claimed_from')},ensure_ascii=False)+'\n')
 return reply
exec(compile(src,'ops/a2a_v16.py','exec'),globals())
_orig_wanted=b['wanted']
def wanted_positive(text):
 text=re.sub(r'[^.!?\n]*(?:사지\s*않|구매하지\s*않|원하지\s*않|필요하지\s*않)[^.!?\n]*[.!?\n]?', '', text)
 return _orig_wanted(text)
b['wanted']=wanted_positive
original_run=run
def run(args,kit):return original_run(args,kit)