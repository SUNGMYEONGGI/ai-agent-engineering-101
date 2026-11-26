def test(run,kit):
 assert run({'word':''},kit)=={'matches':[],'count':0}
 assert run({'word':'abc','paths':['tmp/test/no_such_file']},kit)['count']==0
