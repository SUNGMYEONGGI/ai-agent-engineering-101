import json,time,uuid,re,fcntl,datetime
from pathlib import Path
import httpx

ALIASES={'계란':['계란','달걀','유정란'],'둥굴레차':['둥굴레차'],'두부':['두부'],'시금치':['시금치'],'취나물':['취나물'],'총각김치':['총각김치','알타리김치'],'김치':['김치'],'우유':['우유'],'두유':['두유'],'요거트':['요거트','요구르트'],'고등어':['고등어'],'가자미':['가자미'],'생선':['생선','가자미','고등어'],'콩나물':['콩나물'],'커피':['커피','원두','드립백'],'쌀':['쌀','백미'],'생수':['생수'],'스파게티':['스파게티','파스타']}
WALLET='결제서는 Hermes Shop 지갑 0x593F…F00C로 서명했습니다(에이전트 카드 wallets.shop과 같음).'
FOOD='식품의 시장 인증서에는 등급이 없으며 식품 등급은 남은 소비기한을 따릅니다. 안내 등급은 현재 재고 기준입니다.'
def path(a,k,d,testing):
 p=Path(a.get(k,d))
 if testing:
  if p.is_absolute() or '..' in p.parts or p.parts[:2]!=('tmp','test'):raise ValueError('invalid test path')
 elif str(p)!=d:raise ValueError('invalid path')
 return p
def stamp(x):
 try:return float(x or 0)
 except Exception:
  try:return datetime.datetime.fromisoformat(str(x).replace('Z','+00:00')).timestamp()
  except Exception:return 0
def log(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a',encoding='utf8') as f:f.write(json.dumps(x,ensure_ascii=False,default=str)+'\n')
def api(kit,p,body=None):
 r=httpx.request('POST' if body is not None else 'GET',kit.market.rstrip('/')+p,headers={'Authorization':'Bearer '+kit.token('shop')},json=body,timeout=8);r.raise_for_status();return r.json()
def settled(x):
 return isinstance(x,dict) and (x.get('settled') is True or x.get('status')=='settled' or x.get('state')=='settled' or settled(x.get('result')) or settled(x.get('data')))
def requests(text):
 hits=[]
 for n,words in ALIASES.items():
  for w in words:
   for m in re.finditer(re.escape(w),text,re.I):hits.append((m.start(),m.end(),n))
 hits.sort(key=lambda z:(z[0],z[0]-z[1]));used=[];out=[]
 for s,e,n in hits:
  if any(s<y and e>x for x,y in used):continue
  used.append((s,e));tail=text[e:e+30]
  if re.match(r'\s*(?:은|는|이|가)?\s*(?:찾는\s*게\s*아니|찾지|말고|아니|안\s*찾|재고\s*확인이\s*안)',tail):continue
  g=re.search(r'(?<![a-z])([ABC])\s*(?:등급|급)',tail,re.I)
  if n not in [z[0] for z in out]:out.append((n,g.group(1).upper() if g else None))
 return out
def matches(n,x):
 name=str(x.get('name','')).lower();return any(w.lower() in name for w in ALIASES[n])
def run(a,kit):
 text=str(a.get('text') or '');data=a.get('data') if isinstance(a.get('data'),dict) else {};now=time.time();lp=None
 try:
  cp=path(a,'catalog_path','public/catalog.json',kit.testing);hp=path(a,'holds_path','holds.json',kit.testing);lp=path(a,'customers_path','customers.jsonl',kit.testing);wp=path(a,'wanted_path','wanted.jsonl',kit.testing)
  if any(k in data for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):
   keys=('order','checkout_jwt','checkout_mandate','payment_mandate');pm=data.get('payment_mandate');core=pm.get('mandate',{}) if isinstance(pm,dict) else {}
   if not all(data.get(k) for k in keys) or not all(core.get(k) for k in ('tx_hash','fee_tx_hash')):r={'reply':'다시 송금하지 마시고 주문서와 결제·수수료 거래가 포함된 mandate를 보내 주세요.','state':'input_required'}
   else:
    try:b=a.get('settle_fixture',{'settled':True}) if kit.testing else api(kit,'/api/settle',{k:data[k] for k in keys});ok=settled(b)
    except Exception:ok=False
    r={'reply':'정산이 완료되었습니다. 감사합니다.' if ok else '정산을 확인하지 못했습니다. 다시 송금하지 말고 같은 주문 번호로 문의해 주세요.','data':{'order':data['order'],'settled':ok},'state':'completed' if ok else 'input_required'}
  elif re.search('환불|파손|보증\\s*청구',text):r={'reply':'주문 번호와 원결제 거래 해시를 알려 주세요. 장부에서 확인하겠습니다. 추가 송금은 하지 마세요.','state':'input_required'}
  else:
   items=json.loads(cp.read_text(encoding='utf8')).get('items',[]);inv=a.get('inventory_fixture',{}) if kit.testing else api(kit,'/api/inventory');units=inv.get('units',[]);choices=[];seen=set()
   for x in items:
    key=str(x.get('sku'))+':'+str(x.get('grade'))
    if key not in seen and type(x.get('price')) is int and x['price']>0 and any(u.get('sku')==x.get('sku') and u.get('grade')==x.get('grade') for u in units):seen.add(key);choices.append({'value':key,'description':str(x.get('name'))+', '+str(x.get('grade'))+', '+str(x.get('price'))})
   choices.append({'value':'none','description':'we do not have it'})
   if kit.testing:dec=a.get('decision_fixture',{})
   else:
    try:
     q={'input':text,'questions':[{'type':'choice','name':'sku','instructions':'구매자가 원하는 상품과 등급을 고르세요. 제외한 상품과 포장 조건을 지키세요. 여러 품목이면 가장 명확한 품목을 고르세요.','choices':choices}]};z=httpx.post('http://127.0.0.1:18790/v1/decisions',json=q,timeout=10);z.raise_for_status();dec=z.json()
    except Exception:dec={}
   ans=(dec.get('answers') or [{}])[0];choice=ans.get('choice');prob=ans.get('probability',ans.get('confidence',0))
   if isinstance(choice,dict):prob=choice.get('probability',choice.get('confidence',prob));choice=choice.get('value')
   probs=ans.get('probabilities',{})
   if isinstance(probs,dict):prob=probs.get(choice,prob)
   try:prob=float(prob)
   except Exception:prob=0
   hp.parent.mkdir(parents=True,exist_ok=True)
   with hp.open('a+',encoding='utf8') as f:
    fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
    try:holds=json.load(f)
    except Exception:holds={}
    now=time.time();holds={k:v for k,v in holds.items() if isinstance(v,dict) and stamp(v.get('expires_at',v.get('until')))>now};fresh=(a.get('fresh_inventory_fixture',inv) if kit.testing else api(kit,'/api/inventory')).get('units',[]);live=[];available=[]
    for u in fresh:
     uid=u.get('unit');ex=stamp(u.get('expires_at'));status=str(u.get('status','')).lower()
     if not uid or uid in holds or u.get('sold') or u.get('held') or status in ('sold','settled','expired','held') or (ex and ex<=now+180) or not u.get('cert'):continue
     live.append(u)
     for x in items:
      if x.get('sku')==u.get('sku') and str(x.get('grade','')).upper()==str(u.get('grade','')).upper() and type(x.get('price')) is int and x['price']>0 and x.get('name'):available.append((x,u));break
    available.sort(key=lambda z:(stamp(z[1].get('expires_at')) or float('inf'),stamp(z[1].get('supplied_at'))));selected=[];missing=[];unpriced=[];req=requests(text)
    if prob>=0.6 and choice and choice!='none':
     picks=[z for z in available if str(z[0]['sku'])+':'+str(z[0]['grade'])==choice]
     if picks and (not req or any(matches(n,picks[0][0]) and (not g or g==picks[0][1]['grade']) for n,g in req)):selected.append(picks[0])
    for n,g in req:
     if any(matches(n,x) and (not g or u.get('grade')==g) for x,u in selected):continue
     candidates=[z for z in available if matches(n,z[0]) and (not g or z[1].get('grade')==g) and z[1]['unit'] not in [p[1]['unit'] for p in selected]]
     if n=='두부' and re.search('멸균두부.{0,5}(?:제외|말고)|연두부.{0,5}(?:제외|말고)',text):candidates=[z for z in candidates if not re.search('멸균두부|연두부',z[0]['name'])]
     if n=='커피' and re.search('드립백|원두',text):candidates=[z for z in candidates if re.search('드립백|원두',z[0]['name'])]
     if candidates:selected.append(candidates[0]);continue
     held=[u for u in live if matches(n,u) and (not g or u.get('grade')==g)]
     if held:unpriced.append(n);continue
     missing.append(n+((' '+g+'등급') if g else ''));log(wp,{'at':now,'item':n,'text':text})
    out=[];lines=[];no_checkout=bool(re.search('결제서.{0,12}(?:보내지|발급하지|주지)\s*말',text))
    for x,u in selected:
     ex=stamp(u.get('expires_at'));date=datetime.datetime.fromtimestamp(ex,datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M KST') if ex else '표시 없음';remaining=(' (약 %.1f시간 남음)'%((ex-now)/3600)) if ex else '';line='%s / %s등급 / %s credits / 소비기한 %s%s / 보증 %s시간.'%(x['name'],u['grade'],x['price'],date,remaining,x.get('warranty_hours',0))
     if '취나물' in x['name'] and re.search('중량|무게|포장량|몇 g',text,re.I) and not re.search(r'\d+\s*(?:g|kg|그램)',x['name'],re.I):line+=' 포장 중량은 확인되지 않았습니다.'
     if not no_checkout:
      cid=str(uuid.uuid4());task=str(uuid.uuid4());payload={'id':cid,'shop':kit.name,'shop_url':kit.shop_url,'item':x['sku'],'price':x['price'],'task':task,'currency':'credits','iat':int(now),'unit':u['unit'],'cert':u['cert'],'warranty_hours':x.get('warranty_hours',0)};jwt=kit.sign_jwt(payload,'shop');holds[u['unit']]={'expires_at':now+180,'checkout_id':cid,'task':task};out.append({'checkout_jwt':jwt,'unit':u['unit'],'price':x['price'],'sku':x['sku'],'name':x['name'],'grade':u['grade'],'expires_at':u.get('expires_at'),'warranty_hours':x.get('warranty_hours',0),'hold_until':int(now+180)});line+=' 결제서 180초 보류.'
     lines.append(line)
    f.seek(0);f.truncate();json.dump(holds,f,ensure_ascii=False);f.flush();fcntl.flock(f,fcntl.LOCK_UN)
   if missing:lines.append('요청 조건의 재고를 확인하지 못한 품목: '+', '.join(missing)+'.')
   if unpriced:lines.append('실재고는 있으나 현재 판매 가격을 확인 중인 품목: '+', '.join(unpriced)+'. 가격 확인 후 결제서를 드립니다.')
   if not selected and not missing and not unpriced:
    alts=[]
    for x,u in available:
     s='%s %s등급 %s credits'%(x['name'],u['grade'],x['price'])
     if s not in alts:alts.append(s)
     if len(alts)==2:break
    lines.append('요청을 정확히 확인하지 못했습니다.'+(' 현재 판매 가능한 대안: '+' · '.join(alts) if alts else ' 현재 판매 가능한 재고가 없습니다.'))
   lines.append(WALLET)
   if any(u.get('kind')=='food' for x,u in selected):lines.append(FOOD)
   r={'reply':'\n'.join(lines),'data':{'checkouts':out},'state':'input_required'}
   if len(out)==1:r['data'].update(out[0])
  log(lp,{'at':now,'text':text,'data':data,'reply':r['reply'],'response_data':r.get('data'),'task_id':a.get('task_id'),'claimed_from':a.get('claimed_from')});return r
 except Exception as e:
  if lp:
   try:log(lp,{'at':now,'text':text,'reply':'재고를 확인하지 못했습니다. 잠시 뒤 다시 문의해 주세요.','error':str(e)})
   except Exception:pass
  return {'reply':'재고를 확인하지 못했습니다. 잠시 뒤 다시 문의해 주세요.','state':'input_required'}
