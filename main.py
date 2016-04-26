import sys, logging, time, os, random
from multiprocessing import Process,Pipe
import threading
from threading import Thread
from loop import operate_conn
import json 
import msghandler 
import signal
import traceback
from constants import * 

'''
	the format of processes 
	{
		process(required) : the process arg 
		process_hold_by_sub (optional) : the pipe object hold by sub process 
		process_hold_by_main (optional) : the pipe object hold by main process
	}
'''

'''
	the format of processlist.json 
	{
		name:  item name in processes 
		{
			"package": the package that function of this process contained
			"function": function name 
			"args":[{"type":"variable","value":"SERVER_ADDR"}] arg example 
			"need_pipe" : whether the process need the communicate with main process 
			"msg_handler_name"(optional) : the name of message handler function \
								, contains in the package msghandler , \
								default name is nameMsgHandler  
		}
	}
'''

# global SERVER_ADDR
# SERVER_ADDR = "ws://localhost:8088/worker"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

global shouldTerminate
shouldTerminate = False

global processes

def getMsgHandler(func,callback=None):
	def handle(conn,processItem,processName):
		while True and not shouldTerminate: 
			msg = conn.recv()
			func(msg,processItem,processName)
			if callback : 
				callback(msg)
		print 'thread ',threading.current_thread(),' terminate'
	return handle 

def getProcessList():
	return json.load(open('./processlist.json','r+'))


def initProcesses():
	processlist = getProcessList()
	processes = {}
	package_msg_handler = globals()['msghandler']
	for k,v in processlist.items() : 
		print v
		package = v['package']
		func = v['function']
		defaultArgs = v['args']
		args = []
		need_pipe = v['need_pipe']
		msg_handler_name = v.get('msg_handler_name')
		if not msg_handler_name : 
			msg_handler_name = "%sMsgHandler"%k
		if not globals().get(package) :
			try : 
				package = __import__(package)
				func = getattr(package,func)
				for arg in defaultArgs : 
					print arg 
					if arg['type'] == 'variable' : 
						arg = globals()[arg['value']]
						args.append(arg)
				# processes[k] = Process(target = func,args = args)
				# processes[k].start()
				processes[k] = {}
				if need_pipe : 
					processes[k]['pipe_hold_by_main'],processes[k]['pipe_hold_by_sub'] = Pipe()
					processes[k]['msg_handler'] = getattr(package_msg_handler,msg_handler_name)
					args.append(processes[k]['pipe_hold_by_sub'])
				args = tuple(args)
				processes[k]['process'] = Process(target = func,args = args)
				processes[k]['process'].start()
				processes[k]['args'] = args
				if processes[k].get('msg_handler') : 
					processes[k]['msg_handler_thread'] = Thread(target = getMsgHandler(processes[k]['msg_handler']),args=(processes[k]['pipe_hold_by_main'],processes[k],k))
					processes[k]['msg_handler_thread'].daemon = False
					processes[k]['msg_handler_thread'].start()
					logger.info("Msg handler thread for %s start now "%k)
			except Exception,e : 
				traceback.print_exc()
				continue
	return processes


def terminateSubprocessesAndMonitor():
	print 'current thread ',threading.current_thread()
	shouldTerminate = True
	if not processes : 
		print 'processes has not been initiated'
		return 
	for processName in processes:
		process = processes[processName]
		if 'process' in process:
			print 'terminate process ',processName
			process['process'].terminate()

def inthandler(signum,frame):
	#terminateSubprocessesAndMonitor()
	os._exit(1)
signal.signal(signal.SIGINT,inthandler)
processes = initProcesses()







