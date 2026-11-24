def run(args,kit):
    text='RULES\n'+str(args.get('rules',''))+'\n\nNOW\n'+str(args.get('now',''))+'\n\nFAILED\n'+str(args.get('failed',''))
    text=text[:2490]
    with open('notes.md','w',encoding='utf8') as f: f.write(text)
    return {'written':True,'chars':len(text)}
