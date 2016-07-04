from zope.interface import Interface

"""
The interface for task
"""
class ITask(Interface):
	def run(optype,params,timeout=10000,callback=None):
		"""
		run the task 
		"""

	def execute(optype,params,timeout=10000):
		"""
		execute the task
		return the task result 
		"""

	def parseResult(optype,result):
		"""
		parse the result returned by task
		"""
		
	# def timeout(timeout=10000):
	# 	"""
	# 	invoke when task timeout
	# 	"""

class IParser(Interface):
	"""docstring for IParser"""
	def compile(regexs):
		"""
		compile the regular expressions
		"""
	def parse(str):
		"""
		parse the string to a dictionary
		"""
		
