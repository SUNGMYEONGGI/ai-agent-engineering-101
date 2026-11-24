import os, json
def test(run,kit):
    r=run({'items':[{'sku':'x','grade':'A','price':100}],'buying':'예약'},kit)
    assert r['written'] and os.path.exists('card.json')
    assert json.load(open('card.json',encoding='utf8'))['language']=='ko'
