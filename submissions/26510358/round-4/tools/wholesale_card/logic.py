import httpx
def run(a,kit):
 try:
  if kit.testing:return {'ok':True,'card':a['fixture']}
  r=httpx.get(kit.market.rstrip('/')+'/entities/wholesale/.well-known/agent-card.json',timeout=12);r.raise_for_status();return {'ok':True,'card':r.json()}
 except Exception as e:return {'ok':False,'error':str(e)}