# import subprocess
# import shlex
# import os
# import json
# import time
# import threading

# from tasks import CmdTask
# runningtask={}
# taskHandler = CmdTask(os.path.join(os.path.dirname(__file__),'optypes.json'))
# task = json.load(open("input.json","r+"))
# optype = task['optype']
# params = task
# threading.Thread(target=taskHandler.run,args=(optype,params,20))
# runningtask[task['taskId']]=taskHandler
# time.sleep(10)
# print "after sleep"
# a=runningtask.get(task['taskId'])
# a.terminate = True
# import sys
# import msghandler.gitutil as gitutil
# from threading import Thread
# import time
# import json
# import config


#print gitutil.getCurrentVersion(sys.path[0])
# def showVersionIds():
# 	versions = gitutil.getVersionList(sys.path[0])
# 	for v in versions : 
# 		print v.id 

# print 'current version is ',gitutil.getCurrentVersion(sys.path[0])
# gitutil.updateToLatestVersion(sys.path[0])
# print 'current version is ',gitutil.getCurrentVersion(sys.path[0])
#print json.dumps(gitutil.getVersionList(config.APPLICATION_PATH),indent=4,ensure_ascii=False)
# print gitutil.getCurrentVersion(config.APPLICATION_PATH).__str__()
import tasks
print tasks.tracerouteToDest("bbs.byr.cn")




