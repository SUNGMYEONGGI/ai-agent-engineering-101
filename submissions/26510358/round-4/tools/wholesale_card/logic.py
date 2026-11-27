import httpx

def run(a,kit):
 try:
  entity=a.get('entity','wholesale');assert entity in ('clearing','orders','wholesale','forum')
  if kit.testing:card=a['fixture']
  else:
   r=httpx.get(kit.market.rstrip('/')+'/entities/'+entity+'/.well-known/agent-card.json',timeout=12);r.raise_for_status();card=r.json()
  assert isinstance(card,dict) and isinstance(card.get('skills'),list)
  return {'ok':True,'card':card}
 except Exception as e:return {'ok':False,'error':str(e)}