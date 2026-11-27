from pathlib import Path

def test(run,kit):
 root=Path('tmp/test');root.mkdir(parents=True,exist_ok=True);p=root/'wanted_retry';inv={'units':[{'unit_id':'live','name':'계란 20구','sku':'egg','grade':'B','price':7000},{'unit_id':'gone','name':'두부','sku':'tofu','grade':'A','price':2000,'status':'sold'}]};a={'inventory_fixture':inv,'wanted_path':str(p),'holds_path':str(root/'holds_retry')}
 r=run(dict(a,text='계란 B등급 있나요?'),kit);assert '계란 20구' in r['reply'] and 'B등급' in r['reply'] and '7000크레딧' in r['reply'] and r['data']['checkouts'][0]['unit_id']=='live'
 r=run(dict(a,text='두부 있나요?'),kit);assert '확인되지 않습니다' in r['reply']
 r=run(dict(a,text='시금치 있나요?'),kit);assert p.exists() and '시금치' in p.read_text(encoding='utf8')
