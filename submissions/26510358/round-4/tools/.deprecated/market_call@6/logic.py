import httpx, json

def run(args, kit):
    if kit.testing:
        return {'status':200,'body':{'ok':True,'test':True}}
    base=args.get('url') or kit.market
    path=args.get('path','/')
    url=path if path.startswith('http') else base.rstrip('/')+'/'+path.lstrip('/')
    headers={}
    auth=args.get('auth','none')
    if auth in ('shop','buyer'):
        headers['Authorization']='Bearer '+kit.token(auth)
    try:
        r=httpx.request(args.get('method','GET').upper(),url,headers=headers,json=args.get('body'),timeout=25,follow_redirects=True)
        try: body=r.json()
        except Exception: body={'text':r.text[:1500]}
        return {'status':r.status_code,'body':body}
    except Exception as e:
        return {'status':599,'body':{'error':str(e)[:500]}}
