def run(args,kit):
 word=str(args.get('word','')).lower(); out=[]
 if not word:return {'matches':[],'count':0}
 for path in args.get('paths',['logs/react.jsonl','logs/agent-kit.log']):
  try:
   with open(path,encoding='utf8') as f:
    for line in f:
     if word in line.lower():out.append({'file':path,'line':line.rstrip()})
  except (OSError,UnicodeError):pass
 return {'matches':out[-50:],'count':len(out)}
