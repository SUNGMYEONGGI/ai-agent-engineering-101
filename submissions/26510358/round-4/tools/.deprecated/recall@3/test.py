def test(run,kit):
 assert run({'word':''},kit)=={'matches':[],'count':0}
 assert run({'word':'abc','paths':['tmp/test/absent']},kit)['count']==0
