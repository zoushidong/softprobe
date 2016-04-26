from autobahn.twisted.websocket import WebSocketClientProtocol,WebSocketClientFactory,connectWS
from twisted.internet import reactor,threads
from twisted.internet.protocol import ReconnectingClientFactory
# from twisted.internet.utils import getProcessOutput
from tasks import CmdTask,tracerouteToDest
import os
import json
import psutil
import config
from config import * 
#from snmp import hostSysInfo
import time
from utils import * 
from arp import getArpInfo
from task_process import *
from threading import Thread 
#import msghandler as gitutil 
from msghandler import gitutil
import subprocess
import constants



HEARTBEAT_INTERVAL = 60
runningTask={}
arpNeighbors = getArpInfo()
lastNetIo = {"sent":0,"recv":0}
PIPE = None 
global facotry
facotry = None
try : 
	version = json.load(open('version.json','r'))['version']
except Exception,e : 
	version = constants.SYS_VERSION

def sendInfoToPipe(info):
	if PIPE : 
		PIPE.send(info)
	else:
		print 'no pipe'

def executeTask(task):
	taskHandler = CmdTask(os.path.join(os.path.dirname(__file__),'optypes.json'))
	if task['taskRecordId'] not in runningTask:
		runningTask[task['taskRecordId']] = {}
		runningTask[task['taskRecordId']][task['taskId']]=taskHandler
	else:
		runningTask[task['taskRecordId']][task['taskId']]=taskHandler
	# print runningTask
	optype = task['optype']
	params = task
	if task.get('timeout'):
		timeout = task['timeout']
	else:
		timeout = 20
	result = taskHandler.run(optype,params,timeout)
	print result
	return result

def executeTraceroute(result):
	data = tracerouteToDest(result['destination'])
	result['tracedata'] = data
	print result
	return result


def arpUpdate(data=None):
	if data : 
		arpNeighbors = data
		return
	d = threads.deferToThread(getArpInfo)
	d.addCallback(arpUpdate)
	# reactor.callLater(10*60,arpUpdate)

def getSysInfo(id):
		# hostInfo=None
		# if hostAddr:
		# 	hostInfo = hostSysInfo(self.hostAddr)
		global version
		cpu_percent = psutil.cpu_percent(interval=None)
		mem_usage = psutil.virtual_memory().percent
		if NETWORK_INTERFACE in psutil.net_if_addrs():
			ip = psutil.net_if_addrs()[NETWORK_INTERFACE][0].address
			mask = psutil.net_if_addrs()[NETWORK_INTERFACE][0].netmask
			mac = psutil.net_if_addrs()[NETWORK_INTERFACE][getMacAddressIndex()].address
		else:
			ip = None
			mask = None
			mac = None
		bytes_sent = psutil.net_io_counters().bytes_sent
		bytes_recv = psutil.net_io_counters().bytes_recv
		bytes_sent_avg = round(float(bytes_sent-lastNetIo["sent"])/HEARTBEAT_INTERVAL/1024,2) if bytes_sent-lastNetIo["sent"] > 0 else 0  #Kbytes/s
		bytes_recv_avg = round(float(bytes_recv-lastNetIo["recv"])/HEARTBEAT_INTERVAL/1024,2) if bytes_recv-lastNetIo["recv"] > 0 else 0  #Kbytes/s
		lastNetIo["sent"] = bytes_sent
		lastNetIo["recv"] = bytes_recv
		task_processes = getTaskProcessInfo()
		probeInfo = dict(cpu = cpu_percent, memory = mem_usage,ipaddress=ip,netmask=mask,macaddress=mac,arpNeighbors=arpNeighbors,bytesSent=bytes_sent_avg,bytesRecv=bytes_recv_avg,task_processes=task_processes)
		result = dict(clientId=id,type="heartbeat",time=time.time(),content=probeInfo)
		#result['currentVersion'] = gitutil.getCurrentVersion(config.APPLICATION_PATH).__str__()
		result['currentVersion'] = version
		return result


class ProbeWebsocketClientProtocol(WebSocketClientProtocol):
	needReconnection = False 

	def onConnect(self,response):
		self.hostAddr=''
		self.id=''
		psutil.cpu_percent(interval=None)
		# pass

	def onMessage(self,payload,isBinary):
		task = json.loads(payload)
		if task.get('type') == 'yourId':
			if task['content'] : 
				self.id = task['content']['id']
				self.hostAddr=task['content']['hostAddr']
			if self.id == '':
				self.sendMessage(json.dumps(getSysInfo(self.id)))
			else:
				time.sleep(1)
				self.sendHeartBeat()

		elif task.get('type') == 'version' : 
			print 'send info to pipe '
			sendInfoToPipe(task)

		elif task.get('type') == 'reboot' : 
			print 'reboot now'
			sendInfoToPipe(task)

		elif 'optype' in task: 
			print task
			d = threads.deferToThread(executeTask,task)
			# d = defer.execute(executeTask,task)
			d.addCallback(self.callBack)
			# d.addErrback(self.errorBack)
		elif task.get('type') == 'stop':
			if task.get('taskRecordId'):
				# print task['taskRecordId']
				self.terminate(task['taskRecordId'])

	def onOpen(self):
		self.needReconnection = False

	def onClose(self,wasClean,code,reason):
		print 'connection close'

	def callBack(self,result):
		if result['taskRecordId'] in runningTask:
			if result['taskId'] in runningTask[result['taskRecordId']]:
				del runningTask[result['taskRecordId']][result['taskId']]
			if not runningTask[result['taskRecordId']]:
				del runningTask[result['taskRecordId']]
		# print result
		# self.sendMessage(json.dumps(result))
		self._whether_error_exists(result)

	def sendHeartBeat(self):
		# d = threads.deferToThread(getSysInfo,self.id,self.hostAddr)
		# d.addCallback(self.callBack)
		result = getSysInfo(self.id)
		# print result
		self.sendMessage(json.dumps(result))
		reactor.callLater(HEARTBEAT_INTERVAL,self.sendHeartBeat)

	def sendHostInfo(self):
		# hostInfo = hostSysInfo(self.hostAddr)
		# result = dict(clientId = self.id, type = "hostInfo", content = hostInfo,time=time.time())
		# print result
		# self.sendMessage(json.dumps(result))
		# reactor.callLater(2*60,self.sendHostInfo)
		pass

	def terminate(self,taskRecordId):
		if taskRecordId in runningTask:
			for taskHandler in runningTask[taskRecordId].values():
				taskHandler.terminate = True
		else:
			print "the task was already terminated"
			# self.sendMessage(json.dumps(dict(status="fail",clientId=self.id,taskId=taskId,content="the task was already terminated")))

	def _whether_error_exists(self,result):
		is_error_exists = False
		if not result.get('optype') or result['optype'] == 'iperf-s' or result['optype'] == 'iperf-close': 
			self.sendMessage(json.dumps(result))
			return
		if result['status'] == 'fail' : 
			is_error_exists = True
		elif result['type'] == 'ttl' : 
			if not result['result']['rtt'] or (float(result['result']['rtt']) >= result['threshold'] ):
				is_error_exists = True
		elif result['type'] == 'loss' : 
			if not result['result']['packet loss'] or (float(result['result']['rtt']) >= result['threshold']) : 
				is_error_exists = True 
		elif result['type'] == 'bandwidth' :
			if not result['result']['bandwidth'] : 
				is_error_exists = True
			else : 
				bandwidth = result['result']['bandwidth'].split(' ')[0]
				if float(bandwidth) < result['threshold'] : 
					is_error_exists = True
		
		# if is_error_exists : 
		# 	if not result['status'] == 'fail' : 
		# 		result['status'] = 'abnormal'
		# 	d = threads.deferToThread(executeTraceroute,result)
		# 	d.addCallback(lambda x : self.sendMessage(json.dumps(x)))
		# else : 
		self.sendMessage(json.dumps(result))

		


class MyWebSocketClientFactory(WebSocketClientFactory,ReconnectingClientFactory):

	protocolInstance = None

	def buildProtocol(self,address):
		proto = WebSocketClientFactory.buildProtocol(self,address)
		self.protocolInstance = proto
		return proto

	def clientConnectionLost(self,connector,reason):
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

	def clientConnectionFailed(self,connector,reason):
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

	def sendMessage(self,message):
		if self.protocolInstance : 
			if isinstance(message,dict):
				self.protocolInstance.sendMessage(json.dumps(message,ensure_ascii=False))
			elif isinstance(message,str) or isinstance(message,unicode) : 
				self.protocolInstance.sendMessage(message)
#facotry = WebSocketClientFactory("ws://210.25.137.240:8088/worker")

def handlerMessage():
	while True : 
		msg = PIPE.recv()
		trigger =  msg.get('trigger')
		if not facotry : 
			return 
		if trigger['type'] == 'version' :
			reply = {}
			reply['type'] = trigger['type']
			reply['op'] = trigger['op']
			reply['currentVersion'] = msg.get('extra').get('currentVersion')
			if msg.get('type') == 'op_status' : 
				reply['status'] = msg.get('result')
			else : 
				data = msg.get('value')
				if data : 
					reply['status'] = 'success'
					reply['data'] = data
				else : 
					reply['data'] = None 
					reply['status'] = False
		facotry.sendMessage(reply)




		

def operate_conn(serverAddr,pipe=None):
	'''
		operate the conmunicate with server 
	'''
	globals()['PIPE'] = pipe # change the global variable PIPE

	print 'pipe is ',pipe
	if pipe : 
		print 'monitor start'
		monitor = Thread(target = handlerMessage)
		monitor.daemon = True
		monitor.start()

	facotry = MyWebSocketClientFactory(serverAddr)
	facotry.protocol = ProbeWebsocketClientProtocol
	connectWS(facotry)
	arpUpdate()
	reactor.run()

if __name__ == '__main__' :
	operate_conn("ws://210.25.137.240:8088/worker")


