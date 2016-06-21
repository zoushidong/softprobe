# encoding: utf-8
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
import datetime



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
	#print 'executeTask',task
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
	if task['optype'] == 'ping':
		rawresult,traceresult = tracerouteToDest(task['destination'])
		result['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		if traceresult:
			result['trace_result'] = traceresult
			result['trace_rawresult'] = rawresult
	return result

def executeTraceroute(task):
	result = {}
	result['sched_type'] = task['sched_type']
	result['optype'] = task['optype']
	result['taskId'] = task['taskId']
	result['clientId'] = task['clientId']
	result['destination'] = task['destination']
	result['createTime'] = task['createTime']
	result['startTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	result['taskRecordId'] = task.get('taskRecordId')
	result['jobId'] = task.get('jobId')
	result['interval'] = task.get('interval')
	result['type'] = task.get('type')
	
	rawresult,traceresult = tracerouteToDest(task['destination'])
	result['endTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	if traceresult:
		result['status'] = 'success'
		result['trace_result'] = traceresult
		result['trace_rawresult'] = rawresult
	else:
		result['status'] = 'failed'
		result['trace_result'] = []
		result['trace_rawresult'] = ''
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
		license_key = os.getenv('license_key')
		if NETWORK_INTERFACE in psutil.net_if_addrs():
			ip = psutil.net_if_addrs()[NETWORK_INTERFACE][0].address
			mask = psutil.net_if_addrs()[NETWORK_INTERFACE][0].netmask
			mac = psutil.net_if_addrs()[NETWORK_INTERFACE][getMacAddressIndex()].address
			ipv6address = getIpv6Address()
		else:
			ip = None
			mask = None
			mac = None
			ipv6address = []
		bytes_sent = psutil.net_io_counters().bytes_sent
		bytes_recv = psutil.net_io_counters().bytes_recv
		bytes_sent_avg = round(float(bytes_sent-lastNetIo["sent"])/HEARTBEAT_INTERVAL/1024,2) if bytes_sent-lastNetIo["sent"] > 0 else 0  #Kbytes/s
		bytes_recv_avg = round(float(bytes_recv-lastNetIo["recv"])/HEARTBEAT_INTERVAL/1024,2) if bytes_recv-lastNetIo["recv"] > 0 else 0  #Kbytes/s
		lastNetIo["sent"] = bytes_sent
		lastNetIo["recv"] = bytes_recv
		task_processes = getTaskProcessInfo()
		topTotal,processs = getProgress()
		probeInfo = dict(cpu = cpu_percent, memory = mem_usage,ipaddress=ip,device_type = 'hard',ipv6address=ipv6address,toptotal=topTotal,topprocess=processs,license_key=license_key,netmask=mask,macaddress=mac,arpNeighbors=arpNeighbors,bytesSent=bytes_sent_avg,bytesRecv=bytes_recv_avg,task_processes=task_processes)
		result = dict(clientId=id,type="heartbeat",time=time.time(),content=probeInfo)
		#result['currentVersion'] = gitutil.getCurrentVersion(config.APPLICATION_PATH).__str__()
		result['currentVersion'] = version
		return result

def getIpv6Address():
	ipv6 = []	
	for index in range(len(psutil.net_if_addrs()[NETWORK_INTERFACE])):
		address = psutil.net_if_addrs()[NETWORK_INTERFACE][index].address
		if index == 0 or 'fe80::' in address or len(address) == 17:
			pass
		else: 
			ipv6.append(address)
	return ipv6
		
def getProgress():
	return '',''
	cmd = 'top -bn 1'
	cmd = shlex.split(cmd.strip())
	pipe = subprocess.Popen(cmd,stdin = subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	i = 0 
	while i < 10:
		if pipe.poll() is None:
			time.sleep(5)
			i += 1
		else:
			stdoutdata,stderrordata = pipe.communicate()
			break
	else:
		return '','{}'		
	return sortAndGetMaxCpu(stdoutdata)
	
#按照cpu排序，如果剩余的cpu为0.0，则继续按照内存排序，返回CPU内存利用率前15名	
def sortAndGetMaxCpu(out):
	lines = out.split('\n')
	topTotal = ''
	processs = []
	for i in range(5):
		topTotal +=lines[i]+'\n'
	lines = lines[7::]
	#去除cpu 内存利用率都为0.0的进程
	for line in lines:
		process = line.split(' ')
		process = [one for one in process if one !='']
		if len(line)!=0 and (process[8]!='0.0' or process[9]!='0.0'):
			processs.append(process)
	#排序
	result = []
	sort = 8
	nextsort = 9
	for i in range(15):
		max = processs[0][sort]
		maxprocess = processs[0]
		for process in processs:
			if process[sort]>max:
				max = process[sort]
				maxprocess = process
		processs.remove(maxprocess)
		if max == '0.0':#当剩余的cpu利用率都为0.0则按照内存排序
			sort = nextsort
		#取有用的参数
		process = {}
		process['user'] = maxprocess[1]
		process['cpu_percent'] = maxprocess[8]
		process['mem_usage'] = maxprocess[9]
		process['process'] = maxprocess[11]
		result.append(process)		
	return topTotal,result
	
			
				
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

		#elif task.get('type') == 'version' : 
			#print 'send info to pipe '
			#sendInfoToPipe(task)
		elif task.get('type') == 'update' : 
			gitutil.updateToLatestVersion()
		elif task.get('type') == 'reboot' : 
			print 'reboot now'
			#sendInfoToPipe(task)
			gitutil.reboot()
		elif 'optype' in task: 
			d = threads.deferToThread(executeTask,task)
			# d = defer.execute(executeTask,task)
			d.addCallback(self.callBack)
			
			#if task['optype'] == 'ping':
				#print task
				#d = threads.deferToThread(executeTraceroute,task)
				#d.addCallback(self.callBack)
			# d.addErrback(self.errorBack)
		elif task.get('type') == 'stop':
			if task.get('taskRecordId'):
				# print task['taskRecordId']
				self.terminate(task['taskRecordId'])
		elif task.get('type') == 'reverseSSH' :
			print 'reverseSSH'
			gitutil.reverseSSH(config.REVERSE_SSH_PORT,config.REMOTE_SERVER_IP,config.REMOTE_KEY_PATH)
		elif task.get('type') == 'killreverseSSH':
			gitutil.killReverseSSH()

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
		print result
		# self.sendMessage(json.dumps(result))
		self._whether_error_exists(result)

	def sendHeartBeat(self):
		# d = threads.deferToThread(getSysInfo,self.id,self.hostAddr)
		# d.addCallback(self.callBack)
		result = getSysInfo(self.id)
		#print result
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


