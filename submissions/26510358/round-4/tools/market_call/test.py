import os,json

def test(run,kit):
 os.makedirs('tmp/test',exist_ok=True)
 p='tmp/test/market_customers_summary.jsonl'
 rows=[{'ts':99999,'deal':None,'them':'계란 있나요','you':'있습니다'},{'ts':99998,'deal':{'id':'co-1','unit':'u-1'}},{'ts':99997,'deal':{'id':'co-1','unit':'u-1'}},{'ts':99996,'deal':{'id':'co-1','status':'settled'}},{'ts':95000,'deal':None}]
 with open(p,'w',encoding='utf8') as f:
  for row in rows: f.write(json.dumps(row)+'\n')
 ledger=[{'kind':'supply','ts':99500,'data':{'sku':'G12345678','units':['u-1']}},{'kind':'settle','round':4,'ts':99998,'data':{'shop':kit.shop_url+'/','unit':'u-1','amount':3400,'grade':'A'}},{'kind':'settle','round':4,'ts':95000,'data':{'shop':'other','sku':'G12345678','name':'계란','grade':'B','amount':3000}},{'kind':'settle','round':3,'ts':99998,'data':{'shop':kit.shop_url,'sku':'G12345678','amount':1}}]
 r=run({'mode':'metrics','now':100000,'customers_path':p,'ledger':{'entries':ledger}},kit)
 assert (r['msgs'],r['checkouts'],r['settled'])==(5,1,1)
 assert r['hour']=={'msgs':4,'checkouts':1,'settled':1}
 assert r['top_sales']==[{'sku':'G12345678','name':'계란','sold':2,'median_price':3200,'grade_prices':{'A':3400,'B':3000}}]
 assert run({'path':'/api/chain'},kit)['status']==200
 assert run({'path':'https://other.invalid/api','auth':'shop'},kit)['ok'] is False
