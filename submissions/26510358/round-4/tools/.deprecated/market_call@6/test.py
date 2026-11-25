def test(run, kit):
    x=run({'path':'/api/chain','auth':'none'},kit)
    assert x['status']==200 and 'body' in x
