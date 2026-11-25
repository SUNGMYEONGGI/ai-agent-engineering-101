def test(run, kit):
    r=run({'url':'https://example.com','path':'/sample','method':'GET'},kit)
    assert r['status']==200
    assert r['summary']['ok'] is True
