from pathlib import Path
import re
p=Path('tools/.deprecated/a2a_handler@31/logic.py')
if not p.exists():p=Path('tools/a2a_handler/logic.py')
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),globals())
_previous=run

def _mask_declined(text):
 pat=r'(?:아까는|이전에는|전에|지난번에는)\s*[^.!?\n]{0,80}?(?:안\s*샀어요|안\s*샀습니다|사지\s*않았어요|구매하지\s*않았어요|거절했어요)'
 return re.sub(pat,'이전에 구매를 보류했어요',text)

def run(a,kit):
 text=a.get('text')
 if not isinstance(text,str):return _previous(a,kit)
 filtered=_mask_declined(text)
 if filtered==text:return _previous(a,kit)
 b=dict(a);b['text']=filtered
 return _previous(b,kit)
