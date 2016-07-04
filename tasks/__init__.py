"""
The module for all the tasks probe should execute
"""
from __future__ import unicode_literals
from zope.interface import implementer
from interfaces import * 
import json
import subprocess
import shlex
import types
import utils
import signal
from datetime import datetime
import time
import re
import psutil

def typeParser(name) : 
	 name = utils.ucfirst(name)+"Type"
	 return getattr(types,name)

"""
timeout handler
"""
class TimeoutAlarm(Exception):
	pass

# def timeout_alarm(signum,frame):
#	raise TimeoutAlarm

@implementer(ITask)

class CmdTask:
	def __init__(self,optypesConfigFile=None):
		"""
		init the optype and other parameters
		"""
		if optypesConfigFile:
			self.optypes = json.load(open(optypesConfigFile,"r+"))
		else:
			self.optypes = {}

		self.valueExtractor = None
		self.errorReason = None
		self.startTime = None
		self.endTime = None
		self.terminate = False
		self.attempt = 2
		self.createTime = None

	def run(self,optype,params,timeout=20,callback=None):
		"""
		run the task 
		"""
		#print 'run task:',params
		if optype in self.optypes:
			self.clientId = params.get('clientId')
			self.taskId = params.get('taskId')
			self.jobId = params.get('jobId')
			self.createTime = params.get('createTime')
			self.tot_fragment = params.get('tot_fragment')
			self.fragment = params.get('fragment')
			result = self.execute(optype,params,timeout)
			result['sched_type'] = params['sched_type']
			result['taskRecordId'] = params.get('taskRecordId')
			result['jobId'] = self.jobId
			result['interval'] = params.get('interval')
			result['type'] = params.get('type')
			result['timeout'] = timeout
			if 'rawdestination' in params:
				result['destination'] = params['rawdestination']
			else : 
				result['destination'] = params['destination']
			if callback : 
				callback(result)
			return result 
		else : 
			print 'not in optype'
			return self._error(optype,"Illegal operation type")


	def execute(self,optype,params,timeout):
		"""
		execute the task
		return the task result 
		"""
		while self.attempt>0: 
			self.startTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			cmd = self._cmdArgParser(optype,params)
			if not cmd : 
				return self._error(optype,self.errorReason)
			self.pipe = subprocess.Popen(cmd,stdin = subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			if '-s' in optype:
				timeout = 30
				# while not self.terminate:
				#	continue
				# else:
				#	self.pipe.kill()
				#	return self._success(optype,'terminated successfully')	
			try : 
				i = 0
				while not self.terminate and i < timeout:
					if self.pipe.poll() is None:
						time.sleep(5)
						i += 5
					else:
						stdoutdata,stderrordata = self.pipe.communicate()
						break;
				else:
					self.pipe.terminate()
					if self.terminate:
						# return self._success(optype,'terminated successfully')
						stdoutdata,stderrordata = self.pipe.communicate()
						print "-----task terminate-----"
					else:	
						raise TimeoutAlarm
				self.endTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				if stderrordata : 
					# return self._error(stderrordata)
					self.attempt-=1
					continue
				else : 
					result = self.parseResult(optype,params,stdoutdata)
					for item in result:
						if item is not None:
							break
					else:
						self.attempt-=1
						continue
					# if 'taskId' in params : 
					#	result['taskId'] = params['taskId']
					# if 'clientId' in params : 
					#	result['clientId'] = params['clientId']
					if 'serverId' not in params : 
						return self._success(optype,result)
					else : 
						return self._success(optype,result,params['serverId'])
			
			except TimeoutAlarm,e : 
				return self._error(optype,"Task timeout ...")
		else:
			if stderrordata:
				return self._error(optype,stderrordata)
			else:
				return self._error(optype,"fail execute the task")

	def parseResult(self,optype,params,result):
		"""
		TODO : parse the result returned by task
		"""
		bandwidth = 0
		parseResult={}
		if optype in self.optypes:
			if optype == "iperf-c":
				if "band" in params.get("options"):
					del self.valueExtractor["bandwidth-tcp"]
				else:
					del self.valueExtractor["bandwidth-udp"]
			pattern = self.valueExtractor
		for item in pattern:
			matchResult = re.findall(pattern[item],result,re.M|re.I) ## big character
			item = item.split('-')[0]
			if matchResult:		
				if len(matchResult) == 1:
					parseResult[item] = matchResult[0]
				else:
					if 'bandwidth' in item:
						# print matchResult
						for aResult in matchResult:
							bandwidth += int(float(aResult))
						parseResult[item] = str(bandwidth)
				if 'bandwidth' in item:
					parseResult[item] += ' Mbits/sec'
					#print matchResult.group()
			else:
				parseResult[item] = None
				print item + ": no result"
		return parseResult	

	"""
	return the cmd split by shlex
	return None means have somthing error
	"""
	def _cmdArgParser(self,optype,params):
		ordercmd = {}
		if not self.optypes : 
			self.errorReason = "Legal operation types does no exists"
			return None
		opargs = self.optypes[optype]
		destination = params.get("destination") or ""
		cmd = self.optypes[optype]['cmd']
		self.valueExtractor = opargs.get('valueExtractor')
		options = params.get("options") or None
		if options : 
			for option in options :
				if not options[option]:
					continue
				if option not in opargs['options'] : 
					self.errorReason = "Invalid options type %s"%option
					return None
				optionValidator = opargs['options'][option]
				if type(options[option]) != typeParser(optionValidator['type']):
					# print str(type(options[option]))+str(typeParser(optionValidator['type']))
					self.errorReason = "Inlegal type of option : (%s)"%option
					return None
				op = optionValidator['option']
				v = options[option]
				if v:
					v = str(v)
				else : 
					v = ''
				parameter = (" %s %s"%(op,v))
				ordercmd[parameter] = optionValidator.get('order',100)
		if not options : 
			options = {}
		for option in opargs['options'] : 
			optionValidator = opargs['options'][option]
			# if option not in options and optionValidator['required']:
			if not options.get(option) and optionValidator['required']:	
				if not optionValidator['default'] : 
					self.errorReason = "Lack of required option (%s)"%option
					return None
				else : 
					parameter = " %s %s"%(optionValidator['option'],str(optionValidator['default']))
					ordercmd[parameter] = optionValidator.get('order',100)
		if ordercmd:
			ordercmd = sorted(ordercmd.keys(),cmp=lambda x,y:ordercmd[x]-ordercmd[y])
			print ordercmd 
			for item in ordercmd:
				cmd += item
		cmd += " %s"%destination
		# print shlex.split(cmd.strip())
		print "cmd is "+cmd 
		return shlex.split(cmd.strip())



	def _error(self,optype,reason="Unknown reason!"):
		return self._setTime(dict(status="fail",clientId=self.clientId,taskId=self.taskId,tot_fragment=self.tot_fragment,fragment=self.fragment,optype=optype,result=reason))

	def _success(self,optype,result,serverId=None):
		if not serverId : 
			return self._setTime(dict(status="success",clientId=self.clientId,taskId=self.taskId,tot_fragment=self.tot_fragment,fragment=self.fragment,optype=optype,result=result))
		else : 
			return self._setTime(dict(status="success",clientId=self.clientId,taskId=self.taskId,serverId=serverId,tot_fragment=self.tot_fragment,fragment=self.fragment,optype=optype,result=result))

	def _setTime(self,result):
		if isinstance(result,dict):
			result['startTime'] = self.startTime
			result['createTime'] = self.createTime
			if self.endTime:
				result['endTime'] = self.endTime
			else:
				result['endTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		return result


def tracerouteToDest(dest,selfIp=psutil.net_if_addrs()['eth0'][0].address):
	sp = subprocess.Popen(['traceroute', '-m', '30', '-q', '1', '-n', dest],stdin=subprocess.PIPE,stdout = subprocess.PIPE)
	sp.wait()
	traceresult=[]
	#rtts = []
	rawresult = ''
	for line in sp.stdout:
		rawresult = rawresult + line
		currentresult ={}
		if 'traceroute' in line:
			currentresult['ip'] = selfIp
			currentresult['rtt'] = '0'
			traceresult.append(currentresult)
			#rtts.append(0)
			continue
		if line.find('*') >=0 :
			currentresult['ip'] = '*'
			#rtts.append(0)
			currentresult['rtt'] = '0'
		else :
			cols = line.split('  ')
			currentresult['ip'] = cols[1]
			currentresult['rtt'] = float(cols[2][:-3])
			#rtts.append(float(cols[2][:-3]))
		traceresult.append(currentresult)
	'''
	for index in range(1,len(rtts)-1):
		if rtts[index - 1] != 0:
			result = rtts[index] - rtts[index-1]
			if result > 0:
				traceresult[index]['rtt'] = float(str(rtts[index] - rtts[index-1])[0:6])
			else:
				if rtts[index] != 0:
					traceresult[index]['rtt'] = 0.01
				else:
					traceresult[index]['rtt'] = 0
		else:
			traceresult[index]['rtt'] = rtts[index]
	traceresult[len(rtts)-1]['rtt'] = rtts[len(rtts)-1]
	'''
	return rawresult,traceresult



if __name__ == '__main__' : 
	print tracerouteToDest("www.baidu.com")
