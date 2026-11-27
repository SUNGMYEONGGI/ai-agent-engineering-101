import datetime,fcntl,json,re,time,uuid
from pathlib import Path
import httpx

NOUNS={'둥굴레차':['둥굴레차'],'보리차':['보리차'],'허브차':['허브차'],'스파게티':['스파게티','파스타','아르벨라'],'총각김치':['총각김치','알타리김치'],'김치':['김치'],'취나물':['취나물'],'시금치':['시금치'],'콩나물':['콩나물'],'두부':['두부'],'계란':['계란','달걀','유정란'],'우유':['우유'],'두유':['두유'],'요거트':['요거트','요구르트'],'쌀':['쌀','백미'],'고등어':['고등어'],'가자미':['가자미'],'생선':['가자미','고등어'],'삼겹살':['삼겹살'],'커피':['커피'],'생수':['생수'],'샴푸':['샴푸'],'치약':['치약'],'냉장고':['냉장고'],'즉석조리식품':['즉석조리식품'],'과자':['과자'],'크래커':['크래커']}

def path(a,k,default,testing):
 p=Path(a.get(k,default))
 if testing:
  if p.is_absolute() or '..' in p.parts or p.parts[:2]!=('tmp','test'):raise ValueError('invalid test path')
 elif str(p)!=default:raise ValueError('invalid path')
 return p

def read(p,default):
 try:return json.loads(p.read_text(encoding='utf8'))
 except FileNotFoundError:return default

def append(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a',encoding='utf8') as f:f.write(json.dumps(obj,ensure_ascii=False,default=str)+'\n')

def ts(v):
 try:return float(v or 0)
 except (ValueError,TypeError):
  try:return datetime.datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
  except Exception:return 0

def api(kit,p,body=None):
 return httpx.request('POST' if body is not None else 'GET',kit.market.rstrip('/')+p,headers={'Authorization':'Bearer '+kit.token('shop')},json=body,timeout=8)

def requests(text):
 found=[]; occupied=[]
 for noun,words in sorted(NOUNS.items(),key=lambda v:-max(map(len,v[1]))):
  for w in words:
   for m in re.finditer(re.escape(w),text,re.I):
    if any(m.start()<e and m.end()>s for s,e in occupied):continue
    occupied.append((m.start(),m.end()));found.append((m.start(),m.end(),noun))
 found.sort();out=[]
 for i,(s,e,n) in enumerate(found):
  if n in [x[0] for x in out]:continue
  end=found[i+1][0] if i+1<len(found) else min(len(text),e+45)
  segment=text[e:end]
  g=re.search(r'(?i)([abc])\s*(?:등급|급)',segment)
  out.append((n,g.group(1).upper() if g else None))
 return out

def settled(x):
 return isinstance(x,dict) and (x.get('settled') is True or x.get('status')=='settled' or x.get('state')=='settled' or settled(x.get('result')) or settled(x.get('data')))

def run(a,kit):
 t=time.time(); text=str(a.get('text') or '');data=a.get('data') if isinstance(a.get('data'),dict) else {}
 try:
  cp=path(a,'catalog_path','public/catalog.json',kit.testing);hp=path(a,'holds_path','holds.json',kit.testing);lp=path(a,'customers_path','customers.jsonl',kit.testing);wp=path(a,'wanted_path','wanted.jsonl',kit.testing)
  def work():
   if any(k in data for k in ('payment_mandate','checkout_mandate','tx_hash','fee_tx_hash')):
    keys=('order','checkout_jwt','checkout_mandate','payment_mandate');pm=data.get('payment_mandate');core=pm.get('payload',pm) if isinstance(pm,dict) else None
    if not all(data.get(k) for k in keys) or not isinstance(core,dict) or not all(core.get(k) for k in ('tx_hash','fee_tx_hash')):return {'reply':'다시 송금하지 마시고 주문서와 결제·수수료 거래가 포함된 mandate를 보내 주세요.','state':'input_required'}
    if kit.testing:r=a.get('settle_fixture',{'status':200,'body':{'settled':True}});status=r['status'];body=r['body']
    else:
     r=api(kit,'/api/settle',{k:data[k] for k in keys})
     if r.status_code==503:r=api(kit,'/api/settle',{k:data[k] for k in keys})
     status=r.status_code
     try:body=r.json()
     except Exception:body={}
    ok=200<=status<300 and settled(body)
    return {'reply':'정산이 완료되었습니다. 감사합니다.' if ok else '정산 완료를 확인하지 못했습니다. 다시 송금하지 마시고 같은 주문 번호로 문의해 주세요.','data':{'order':data['order'],'settled':ok,'settle_status':status},'state':'completed' if ok else 'input_required'}
   if re.search(r'환불|파손|보증\s*청구',text):return {'reply':'주문 번호와 원결제 거래 해시를 알려 주세요. 장부에서 확인하겠습니다. 추가 송금은 하지 마세요.','state':'input_required'}
   inv=a.get('inventory_fixture') if kit.testing else None
   if inv is None:
    r=api(kit,'/api/inventory');r.raise_for_status();inv=r.json()
   units=inv.get('units',[]) if isinstance(inv,dict) else []
   items=read(cp,{}).get('items',[])
   hp.parent.mkdir(parents=True,exist_ok=True)
   with hp.open('a+',encoding='utf8') as f:
    fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
    try:holds=json.load(f)
    except Exception:holds={}
    holds={k:v for k,v in holds.items() if isinstance(v,dict) and ts(v.get('expires_at',v.get('until',0)))>t} if isinstance(holds,dict) else {}
    valid=[]
    for x in items:
     if not isinstance(x,dict) or not x.get('sku') or not x.get('name') or type(x.get('price')) is not int or x['price']<=0:continue
     for u in units:
      uid=u.get('unit');expiry=ts(u.get('expires_at'))
      if not uid or uid in holds or u.get('sku')!=x['sku'] or str(u.get('grade','')).upper()!=str(x.get('grade','')).upper() or uid not in x.get('units',[]):continue
      if u.get('sold') or str(u.get('status','')).lower() in ('sold','settled','expired','held') or (expiry and expiry<=t):continue
      valid.append((x,u))
    choices=[];seen=set()
    for x,u in valid:
     key=x['sku']+':'+str(x['grade'])
     if key not in seen:seen.add(key);choices.append({'value':key,'description':x['name']+', '+str(x['grade'])+', '+str(x['price'])})
    choices.append({'value':'none','description':'we do not have it'})
    fixture=a.get('decision_fixture') if kit.testing else None
    try:
     if fixture is None:
      r=httpx.post('http://127.0.0.1:18790/v1/decisions',json={'input':text,'questions':[{'type':'choice','name':'sku','instructions':'구매자가 실제로 원하는 품목과 등급을 고르세요. 거절한 품목은 선택하지 마세요. 불확실하면 none. 여러 상품이면 가장 명시적인 상품 하나.','choices':choices}]},timeout=10);r.raise_for_status();fixture=r.json()
     ans=fixture.get('answers',[{}])[0];choice=ans.get('choice','none');prob=ans.get('probability',ans.get('confidence',0));probs=ans.get('probabilities',{})
     if isinstance(choice,dict):prob=choice.get('probability',choice.get('confidence',prob));choice=choice.get('value','none')
     if isinstance(probs,dict):prob=probs.get(choice,prob)
     if isinstance(probs,list):
      for p in probs:
       if isinstance(p,dict) and p.get('value',p.get('choice'))==choice:prob=p.get('probability',prob)
     prob=float(prob or 0)
    except Exception:choice='none';prob=0
    req=requests(text);selected=[];missing=[];used=set(holds)
    sku=str(data.get('sku') or '')
    m=re.search(r'\bG[0-9a-fA-F]{8}\b',text)
    if not sku and m:sku=m.group()
    if sku:req=[('SKU '+sku,str(data.get('grade') or '').upper() or None)]
    if prob>=0.6 and choice!='none':
     primary=[(x,u) for x,u in valid if x['sku']+':'+str(x['grade'])==choice]
    else:primary=[]
    for noun,grade in req:
     if noun.startswith('SKU '):matches=[(x,u) for x,u in valid if x['sku'].lower()==noun[4:].lower()]
     else:matches=[(x,u) for x,u in valid if any(w.lower() in x['name'].lower() for w in NOUNS[noun])]
     if grade:matches=[(x,u) for x,u in matches if str(x['grade']).upper()==grade]
     if not matches:
      missing.append(noun+((' '+grade+'등급') if grade else ''));append(wp,{'ts':t,'at':int(t),'item':noun,'buyer':a.get('claimed_from')});continue
     if primary and primary[0] in matches:matches=primary+matches
     matches=[z for z in matches if z[1]['unit'] not in used]
     if not matches:continue
     matches.sort(key=lambda z:(ts(z[1].get('expires_at')) or float('inf'),ts(z[1].get('supplied_at'))))
     x,u=matches[0]
     if any(y[0]['sku']==x['sku'] for y in selected):continue
     selected.append((x,u));used.add(u['unit'])
    if not req and primary:
     selected=[primary[0]]
    if not req and not primary:
     alts=[]
     for x,u in valid:
      label=x['name']+' '+str(x['grade'])+'등급 '+str(x['price'])+' credits'
      if label not in alts:alts.append(label)
      if len(alts)==2:break
     return {'reply':('요청하신 상품을 정확히 확인하지 못했습니다. 현재 판매 가능한 상품: '+' · '.join(alts) if alts else '현재 판매 가능한 상품을 확인하지 못했습니다. 상품명을 알려 주세요.'),'state':'input_required'}
    results=[];lines=[];food=False
    for x,u in selected:
     uid=u['unit'];cid=str(uuid.uuid4());task=str(uuid.uuid4());price=x['price']
     payload={'id':cid,'shop':kit.name,'shop_url':kit.shop_url,'item':x['sku'],'price':price,'task':task,'currency':'credits','iat':int(t),'unit':uid,'cert':u.get('cert'),'warranty_hours':x.get('warranty_hours',0)}
     jwt=kit.sign_jwt(payload,'shop');holds[uid]={'expires_at':t+180,'checkout_id':cid,'task':task}
     expiry=ts(u.get('expires_at'));date=datetime.datetime.fromtimestamp(expiry,datetime.timezone(datetime.timedelta(hours=9))).strftime('%m월 %d일 %H:%M KST') if expiry else '표시 없음'
     lines.append(x['name']+' / '+str(x['grade'])+'등급 / '+str(price)+' credits / 소비기한 '+date+' / 보증 '+str(x.get('warranty_hours',0))+'시간. 결제서 180초 보류.')
     if '취나물' in x['name'] and re.search(r'중량|무게|몇\s*(?:g|그램)',text,re.I) and not re.search(r'\d+(?:\.\d+)?\s*(?:kg|g|그램)',x['name'],re.I):lines.append('취나물 포장 중량은 확인되지 않았습니다.')
     food=food or u.get('kind')=='food' or str(x.get('category','')).startswith('식품')
     results.append({'checkout_jwt':jwt,'unit':uid,'price':price,'sku':x['sku'],'name':x['name'],'grade':x['grade'],'expires_at':u.get('expires_at'),'warranty_hours':x.get('warranty_hours',0),'hold_until':int(t+180)})
    if missing:lines.append('현재 결제 가능한 재고를 확인하지 못한 품목: '+', '.join(missing)+'.')
    if results:
     lines.append('결제서는 Hermes Shop 지갑 0x593F…F00C로 서명했습니다(에이전트 카드 wallets.shop과 같음).')
     if food:lines.append('식품의 시장 인증서에는 등급이 없으며 식품 등급은 남은 소비기한을 따릅니다. 안내 등급은 현재 재고 기준입니다.')
    f.seek(0);f.truncate();json.dump(holds,f,ensure_ascii=False);f.flush();fcntl.flock(f,fcntl.LOCK_UN)
    out={'checkouts':results}
    if len(results)==1:out.update(results[0])
    return {'reply':'\n'.join(lines) or '현재 판매 가능한 재고를 확인하지 못했습니다.','data':out,'state':'input_required'}
  result=work();append(lp,{'at':int(t),'text':text,'data':data,'claimed_from':a.get('claimed_from'),'task_id':a.get('task_id'),'context_id':a.get('context_id'),'reply':result});return result
 except Exception as e:
  try:append(path(a,'customers_path','customers.jsonl',kit.testing),{'at':int(t),'text':text,'error':str(e)})
  except Exception:pass
  return {'ok':False,'error':str(e),'reply':'재고 확인에 문제가 생겼습니다. 잠시 후 다시 문의해 주세요.','state':'input_required'}
