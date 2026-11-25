import httpx, json

def run(args, kit):
    if kit.testing: return {'status':200,'body':{'ok':True,'test':True}}
    base=args.get('url') or kit.market
    path=args.get('path','/')
    url=path if path.startswith('http') else base.rstrip('/')+'/'+path.lstrip('/')
    h={}; a=args.get('auth','none')
    if a in ('shop','buyer'): h['Authorization']='Bearer '+kit.token(a)
    r=httpx.request(args.get('method','GET').upper(),url,headers=h,json=args.get('body'),timeout=25)
    try: d=r.json()
    except: d={'text':r.text[:1500]}
    return {'status':r.status_code,'body':d}
