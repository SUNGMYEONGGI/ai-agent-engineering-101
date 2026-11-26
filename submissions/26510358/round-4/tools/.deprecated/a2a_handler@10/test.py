import base64,json,os,time
from unittest.mock import patch

class Resp:
    status_code=200
    is_success=True
    def raise_for_status(self): pass
    def json(self): return {'units':[{'unit':'u-live','sku':'G0746760c','grade':'A','cost':1700,'expires_at':int(time.time())+4000}]}

def test(run,kit):
    p='tmp/test/a2a_v10_'+str(time.time_ns())+'/'
    os.makedirs(p,exist_ok=True)
    a={k+'_path':p+k+'.json' for k in ('catalog','reservations','customers','holds')}
    a.update(context_id='ctx-test',task_id='task-test')
    items=[{'sku':'Gaaaaaaa1','name':'후디스 고단백 무가당 그릭요거트 플레인','grade':'C','price':4990,'stock':1,'units':['u-yogurt']},{'sku':'Gaaaaaaa2','name':'한상궁김치 총각김치 단단한 알타리 무김치','grade':'B','price':8490,'stock':1,'units':['u-kimchi']},{'sku':'G0746760c','name':'동서 둥굴레차 50T 60g','grade':'A','price':3450,'stock':2,'units':['u-stale','u-live']}]
    with open(a['catalog_path'],'w',encoding='utf-8') as f: json.dump({'items':items},f,ensure_ascii=False)
    for msg in ('가정용 냉장고 재고와 배송 설치 조건, 소포장 우유 소비기한 알려 주세요. 판매 가능하면 checkout 보내 주세요.','단단한 두부와 차가 있으면 가격 알려 주세요.','둥굴레차 재고와 가격 알려 주세요.'):
        r=run(dict(a,text=msg),kit)
        assert not r.get('data',{}).get('checkout_jwt') and r.get('ok',True),r
    with patch('httpx.request',return_value=Resp()) as call:
        r=run(dict(a,text='둥굴레차 A등급 구매하겠습니다.'),kit)
        assert call.call_args.args[1].endswith('/api/inventory'),r
    assert r.get('data',{}).get('unit')=='u-live',r
    jwt=r['data']['checkout_jwt']
    h,payload,sig=jwt.split('.')
    def dec(s): return base64.urlsafe_b64decode(s+'='*(-len(s)%4))
    x=json.loads(dec(payload))
    required={'id','shop','shop_url','item','price','task','currency','iat','unit'}
    assert required<=x.keys() and all(x[k] not in ('',None) for k in required)
    assert x['unit']=='u-live' and x['shop']==kit.name and x['shop_url']==kit.shop_url and x['item']=='G0746760c'
    assert json.loads(dec(h))['alg']=='EIP191' and len(dec(sig))==65
    expected=kit.sign_jwt(x,'shop')
    assert jwt==expected
    with open(a['customers_path'],encoding='utf-8') as f: logs=[json.loads(s) for s in f]
    assert len(logs)==4 and all(z['deal'] is None for z in logs[:3]) and logs[3]['deal']['unit']=='u-live'
