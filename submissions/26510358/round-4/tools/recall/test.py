def test(run,kit):
 import os,time
 os.makedirs('logs',exist_ok=True)
 token='unique_recall_'+str(time.time_ns())
 open('logs/react.jsonl','a').write(token+' happened\n')
 x=run({'word':token},kit)
 assert x['count']>=1 and token in x['matches'][-1]['line']
 y=run({'word':'definitely_absent_zzzz'},kit)
 assert y['count']==0