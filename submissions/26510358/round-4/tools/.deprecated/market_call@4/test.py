def test(run, kit):
    assert run({'path':'/api/inventory','method':'GET','auth':'shop'},kit)['status']==200
