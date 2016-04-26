
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from tornado.websocket import WebSocketHandler
from tornado.web import Application
from tornado.web import RequestHandler
import tornado.ioloop
import tornado.options
import tornado.httpserver
from tornado.options import define, options
import tornado.escape
import uuid
define("port", default=8000, help="run on the given port", type=int)

connections = {}

class TaskHandler(object) : 
	def informAll(self,msg):
		for callback in self.callbacks.values() : 
			callback(msg)

	def informOne(self,cbIndex,msg) : 
		callback = self.callbacks.get(cbIndex) 
		if callback : 
			callback(msg)

	def register(self,index,callback): 
		pass

	def unregister(self,index,callback) : 
		pass

	def info(self,type,content) : 
		return dict(type = type,content = content)

"""
Handle the connections between probes
"""
class TaskDispatcher(TaskHandler):
	callbacks = {}
	workers = []
	runningTasks = []
	def __init__(self,app):
		self.app = app

	def register(self,index,callback):
		if not index : 
			index = str(uuid.uuid4())
		self.callbacks[index] = callback
		self.informOne(index,self.info('yourId',index))
		self.app.taskReporter.addWorker(index)
		return index

	def unregister(self,index,callback):
		if index in self.callbacks :
			del self.callbacks[index]
			self.app.taskReporter.deleteWorker(index)
			return True
		else : 
			for c in self.callbacks :
				if self.callbacks[c] == callback : 
					del self.callbacks[c]  
					return True
		return False

	def dispatch(self,task):
		destinationId = task.get('destinationId')
		taskId = task['taskId'] 
		if taskId not in self.runningTasks : 
			self.runningTasks.append(taskId)
			self.informOne(destinationId,task)
			return True


	def feedBack(self,taskId,task) : 
		if taskId in self.runningTasks : 
			self.runningTasks.remove(taskId)
			self.app.taskReporter.taskFinished(taskId,task)



"""
Handle the connections between browsers
"""
class TaskReporter(TaskHandler):
	callbacks = {}
	workers = []
	runningTasks = []
	def __init__(self,app):
		self.app = app

	def addRunningTask(self,task):
		clientId = task['clientId']
		if clientId not in self.callbacks : 
			print "client %s doesnot register"%clientId
			return
		taskId = str(uuid.uuid4())
		if taskId not in self.runningTasks : 
			task['taskId'] = taskId
			self.runningTasks.append(taskId)
			if self.app.taskDispatcher.dispatch(task) : 
				self.informOne(clientId,self.info('taskRunning',dict(workerId = task['destinationId'])))
			else : 
				self.informOne(clientId,self.info('taskFailed','Worker doesnot exist!'))


	def register(self,index,callback) : 
		if not index : 
			index = str(uuid.uuid4())
		self.callbacks[index] = callback
		self.informOne(index,self.info('clientId',index))
		self.informOne(index,self.info('workers',self.workers))
		return index

	def unregister(self,index,callback) : 
		if index in self.callbacks :
			del self.callbacks[index]
			return True
		else : 
			for c in self.callbacks :
				if self.callbacks[c] == callback : 
					del self.callbacks[c]  
					return True
		return False

	"""
	return the task's result to corresponding client depending on task's clientId
	"""
	def taskFinished(self,taskId,result):
		print 'current task id is %s'%taskId
		if taskId in self.runningTasks : 
			clientId = result['result']['clientId']
			if clientId in self.callbacks : 
				self.informOne(clientId,self.info('taskFinished',result))
				self.runningTasks.remove(taskId)
			else : 
				#TODO:持久化存储用户未接收的信息
				pass 

	def addWorker(self,workerId):
		if workerId not in self.workers:
			self.workers.append(workerId)
			self.informAll(self.info('newWorker',workerId))

	def deleteWorker(self,workerId):
		if workerId in self.workers : 
			self.workers.remove(workerId)
			self.informAll(self.info('woekerDelete',workerId))




class WorkerHandler(WebSocketHandler):
	def open(self):
		self.index = self.application.taskDispatcher.register(None,self.callback)

	def on_close(self) : 
		self.application.taskDispatcher.unregister(self.index,self.callback)

	def on_message(self,msg):
		print "%s"%msg
		if isinstance(msg,str) or isinstance(msg,unicode): 
			msg = tornado.escape.json_decode(msg)
		if isinstance(msg,dict):
			self.application.taskDispatcher.feedBack(msg.get('taskId'),msg)

	def callback(self,info):
		self.write_message(info)

class ClientHandler(WebSocketHandler):
	def open(self):
		self.index = self.application.taskReporter.register(None,self.callback)
		print "client connected : %s"%self.index

	def on_close(self):
		self.application.taskReporter.unregister(self.index,self.callback)

	def on_message(self,msg):
		print "%s:%s"%(self.index,msg)
		if isinstance(msg,str) or isinstance(msg,unicode):
			msg = tornado.escape.json_decode(msg)
		if isinstance(msg,dict):
			if not msg.get('clientId') : 
				msg['clientId'] = self.index
			self.application.taskReporter.addRunningTask(msg)
		else : 
			print ">>>> ILLEGAL MESSAGE TYPE <<<<"
	def callback(self,info):
		self.write_message(info)

class IndexHandler(RequestHandler) : 
	def get(self) : 
		self.render('index.html')

class Application(tornado.web.Application):
    def __init__(self):
    	self.taskReporter = TaskReporter(self)
    	self.taskDispatcher = TaskDispatcher(self)
        handlers = [(r'/', IndexHandler),(r'/client', ClientHandler),(r'/worker', WorkerHandler)]

        settings = {'template_path': 'templates','static_path': 'static'}

        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = Application()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

