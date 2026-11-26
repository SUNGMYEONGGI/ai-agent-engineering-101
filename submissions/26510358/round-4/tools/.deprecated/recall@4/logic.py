import json
def run(args,kit):
 word=str(args.get('word','')).lower();out=[]
 if not word:return {'matches':[],'count':0}
 for path in args.get('paths',['logs/react.jsonl','logs/agent-kit.log']):
  try:
   with open(path,encoding='utf8') as f:
    for line in f:
     if word not in line.lower():continue
     if args.get('action') or args.get('tool_name'):
      try:x=json.loads(line)
      except Exception:continue
      if args.get('action') and x.get('action')!=args['action']:continue
      if args.get('tool_name') and x.get('args',{}).get('name')!=args['tool_name']:continue
     out.append({'file':path,'line':line.rstrip()})
  except (OSError,UnicodeError):pass
 if args.get('field') and out:
  x=json.loads(out[-1]['line']);s=x.get('args',{}).get(args['field'],'');off=int(args.get('offset',0));n=int(args.get('length',5000));return {'count':len(out),'total':len(s),'offset':off,'text':s[off:off+n]}
 return {'matches':out[-1:] if args.get('last_only') else out[-50:],'count':len(out)}
