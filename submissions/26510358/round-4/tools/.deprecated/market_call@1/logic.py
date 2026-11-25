import httpx

def run(args, kit):
    if kit.testing:
        return {'status':200,'summary':{'ok':True,'path':args.get('path','/')}}
    url=args.get('url') or kit.market
    path=args.get('path','/')
    target=path if path.startswith('http') else url.rstrip('/')+'/'+path.lstrip('/')
    headers={}
    if args.get('auth'):
        headers['Authorization']='Bearer '+str(args['auth'])
    with httpx.Client(timeout=20) as c:
        r=c.request(args.get('method','GET').upper(),target,headers=headers,json=args.get('body'))
    try: data=r.json()
    except Exception: data=r.text[:1000]
    if isinstance(data,dict): data={k:data[k] for k in list(data)[:20]}
    return {'status':r.status_code,'summary':data}
