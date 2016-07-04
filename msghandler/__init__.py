'''
	all the msg handler defined here
'''

from gitutil import *
import time
import config
from utils import parseArgs
from multiprocessing import Process
import json
import threading
import traceback
from config import *
import subprocess

'''
	the msg format send to subprocess through pipe
	{
		type : op_status | result
		trigger : {
			type : trigger msg type
			op 	: trigger op
		}
		value : success/fail (for op_status)
				the result of operation (for result)
		extra : extra data
	}
'''

def restartProcess(process,processItemFromFile):
	#terminate the process
	process['process'].terminate()

	package = processItemFromFile['package']

	#reload the package contains the function
	module = globals().get(package)
	if module :
		reload(module)
	else :
		module = __import__(package)
		reload(module)

	#get the function
	func = processItemFromFile['function']
	func = getattr(module,func)

	args = parseArgs(processItemFromFile['args'])
	if processItemFromFile['need_pipe'] :
		args.append(process['pipe_hold_by_sub'])
	args = tuple(args)
	process['process'] = Process(target = func,args = args)
	process['process'].start()

def getReturnMessage(rawMsg,result,isStatusReplay=False) :
	msg = {
		'type' : 'result',
		'trigger' : {},
		'value'	  : '',
		'extra'	  :	{}
	}
	if isStatusReplay :
		msg['type'] = 'op_status'
	msg['trigger']['type'] = rawMsg['type']
	if 'optype' in rawMsg :
		msg['trigger']['op'] = rawMsg['optype']
	return msg


def connectionHandlerMsgHandler(msg,processItem,processName):
	#time.sleep(10)
	# print 'monitor thread ',threading.current_thread()
	# processlist = json.load(open(config.PROCESS_LIST_PATH,'r+'))
	# restartProcess(processItem,processlist[processName])
	def feedback(result,isStatusReplay=False) :
		res = getReturnMessage(msg,result,isStatusReplay)
		res['extra']['currentVersion'] = getCurrentVersion().__str__()
		processItem['pipe_hold_by_sub'].send(res)
	print msg
	if msg.get('type') == 'version' :
		op = msg.get('optype')
		if op == 'update' :
			try :
				updateToLatestVersion(config.APPLICATION_PATH)
				processlist = json.load(open(config.PROCESS_LIST_PATH,'r'))
				restartProcess(processItem,processlist['connectionHandler'])
				feedback('success',True)
			except Exception,e :
				traceback.print_exc()
				feedback('fail',True)

		elif op == 'current' :
			feedback(getReturnMessage(msg,getCurrentVersion(config.APPLICATION_PATH).__str__()))

		elif op == 'revert' :
			revert(config.APPLICATION_PATH)
			feedback('success',True)

		elif op == 'changeTo' :
			targetVersion = msg.get('versionName')
			if targetVersion == getCurrentVersion(config.APPLICATION_PATH).__str__() :
				feedback('success',True)
			elif targetVersion in getVersionList(config.APPLICATION_PATH) :
				try :
					changeToVersion(config.APPLICATION_PATH,targetVersion)
					feedback('success',True)
				except Exception,e :
					traceback.print_exc()
					feedback('fail',True)

		else :
			print 'arg error : ',msg
	elif msg.get('type') == 'reboot' : 
		subprocess.Popen(['sudo','reboot'])


def printPath():
	gitutil.printPath()
