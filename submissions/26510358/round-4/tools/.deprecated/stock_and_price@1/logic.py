import os,json,time

def run(args,kit):
 items=args.get('items',[]); sales=args.get('sales',[]); floor=args.get('floor',0)
 os.makedirs('public',exist_ok=True)
 if sales:
  with open('sales.jsonl','a') as f:
   for s in sales: f.write(json.dumps(s,ensure_ascii=False)+'\n')
 out=[]
 for x in items:
  y=dict(x); y['price']=max(int(y.get('price',0)),int(floor)); y['stock']=max(0,int(y.get('stock',0))); out.append(y)
 json.dump({'items':out},open('public/catalog.json','w'),ensure_ascii=False)
 json.dump({'updated':time.time(),'items':out},open('stock.json','w'),ensure_ascii=False)
 return {'ok':True,'items':len(out),'catalog':'public/catalog.json'}
