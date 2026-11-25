def test(run, kit):
 r=run({'to':'0x'+'1'*40,'credits':5,'role':'shop'},kit); assert r['ok'] and r['credit_wei']==1000000000000000 and r['network_fee_credits']==420
 r=run({'to':'0x'+'1'*40,'credits':20001,'role':'shop'},kit); assert not r['ok']
 r=run({'to':'0x'+'1'*40,'credits':5,'role':'buyer'},kit); assert not r['ok']