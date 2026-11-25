def test(run, kit):
 r=run({'to':'0x'+'1'*40,'credits':5,'role':'shop'},kit); assert r['ok']
 r=run({'to':'0x'+'1'*40,'credits':20001,'role':'shop'},kit); assert not r['ok']
