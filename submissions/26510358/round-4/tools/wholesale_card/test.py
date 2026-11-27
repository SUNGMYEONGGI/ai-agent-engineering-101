def test(run,kit):
 for entity in ('clearing','orders','wholesale','forum'):
  r=run({'entity':entity,'fixture':{'skills':[{'id':'supply'}]}},kit);assert r['ok'] and r['card']['skills'][0]['id']=='supply'
 assert not run({'entity':'bad'},kit)['ok']