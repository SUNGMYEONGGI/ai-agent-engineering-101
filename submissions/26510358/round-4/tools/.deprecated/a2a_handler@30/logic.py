from pathlib import Path
import re
p=Path('tools/.deprecated/a2a_handler@29/logic.py')
if not p.exists():p=Path('tools/a2a_handler/logic.py')
s=p.read_text(encoding='utf8')
needle="src=src.replace(base,base+'\\n'+patch,1)"
assert needle in s
s=s.replace(needle,"patch += \"\\nsrc=src.replace('for u in units:\\\\n','for u in units:\\\\n       if cert_required(text) and ((u.get(\\\"cert\\\") or {}).get(\\\"cert\\\") or {}).get(\\\"grade\\\") != u.get(\\\"grade\\\"):continue\\\\n')\"\n"+needle,1)
exec(compile(s,str(p),'exec'),globals())
def cert_required(text):
 return bool(re.search(r'인증서',text) and re.search(r'등급|grade',text,re.I) and re.search(r'명시|표시|명확|같은|null|조건',text,re.I))
b['cert_required']=cert_required
_previous_run=run
def run(a,kit):
 r=_previous_run(a,kit)
 if cert_required(str(a.get('text') or '')) and not (r.get('data') or {}).get('checkouts') and not any(k in (a.get('data') or {}) for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):
  reply=r.get('reply','')
  reply=re.sub(r'([^\n.]+?)(?:은\(는\)|은|는) 없습니다',r'\1의 인증서 등급 조건에 맞는 재고는 없습니다',reply)
  r['reply']=reply+'\n재고의 현재 등급과 도매 원본 인증서의 등급은 다를 수 있습니다. 인증서에 현재 등급이 명시된 상품만 결제서로 드립니다.'
 return r