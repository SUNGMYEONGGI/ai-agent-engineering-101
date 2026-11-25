def test(run, kit):
    r=run({'items':[{'sku':'x','name':'상품','grade':'A','price':10,'stock':2,'warranty_hours':48}],'floor':None},kit)
    assert r['items'][0]['price']==10
    assert r['items'][0]['stock']==2
