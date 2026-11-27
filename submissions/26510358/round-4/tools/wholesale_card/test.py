def test(run,kit):
 c={'skills':[{'id':'supply'}]};r=run({'fixture':c},kit);assert r['ok'] and r['card']['skills'][0]['id']=='supply'