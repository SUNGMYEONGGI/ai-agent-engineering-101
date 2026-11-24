def test(run,kit):
    r=run({'rules':'fees','now':'cards read','failed':'none'},kit)
    assert r['written'] and r['chars']<2500
