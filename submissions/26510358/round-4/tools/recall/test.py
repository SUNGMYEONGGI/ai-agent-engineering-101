def test(run,kit):
 x=run({'word':'anything','paths':['tmp/test/nonexistent_recall_file']},kit);assert x=={'matches':[],'count':0}
 assert run({'word':''},kit)['count']==0
