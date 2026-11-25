import httpx

def run(args, kit):
    if kit.testing:
        return {'status':200,'ok':True,'result':{'test':True}}
    base=args.get('url') or kit.market
    path=args.get('path','/')
    url=path if path.startswith('http') else base.rstrip('/')+'/'+path.lstrip('/')
    headers={}
    auth=args.get('auth','none')
    if auth in ('shop','buyer'):
        headers['Authorization']='Bearer '+kit.token(auth)
    method=args.get('method','GET').upper()
    r=httpx.request(method,url,headers=headers,json=args.get('body'),timeout=25)
    try: data=r.json()
    except: data={'text':r.text[:1000]}
    out={'status':r.status_code}
    if isinstance(data,dict):
        for k in ('ok','result','error','summary','data'):
            if k in data: out[k]=data[k]
    else: out['data']=str(data)[:1000]
    return out
