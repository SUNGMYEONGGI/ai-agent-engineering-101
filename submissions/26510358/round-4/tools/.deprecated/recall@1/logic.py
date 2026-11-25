import os

def run(args,kit):
    word=str(args.get('word','')).lower()
    if not word: return {'matches':[],'count':0}
    out=[]
    for path in ('logs/react.jsonl','logs/agent-kit.log'):
        try:
            with open(path,encoding='utf-8') as f:
                for line in f:
                    if word in line.lower(): out.append({'file':path,'line':line.rstrip()})
        except (FileNotFoundError,PermissionError): pass
    return {'matches':out[-50:],'count':len(out)}
