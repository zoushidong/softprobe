from __future__ import unicode_literals
import config
from constants import *
import subprocess
import shlex
import os
import re
import signal

"""
	return the task_process info :
	{
		cmdline : '',
		pid : '',
		name : ''
	}
"""
def parseTaskProcessInfo(line):
	cols = re.split('\s+',line)
	info = {}
	info['pid'] =cols[1]
	info['name'] = cols[10]
	info['cmdline'] = cols[10:]
	return info

def getTaskProcessInfo():
	pipe1 = subprocess.Popen(shlex.split('ps -aux'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	pipe2=subprocess.Popen(shlex.split('grep -E "[p]ing|[i]perf|[c]url"'),stdin=pipe1.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	stdoutdata,stderrordata = pipe2.communicate()
	if stdoutdata :
		lines = stdoutdata.split(os.linesep)
		taskProcessesInfos = [ parseTaskProcessInfo(line) for line in lines if line]
		return taskProcessesInfos
	return []
def killTaskProcessByPid(pid):
    try:
        a = os.kill(pid, signal.SIGKILL)
    except OSError, e:
        pass


if __name__ == '__main__' :
	print getTaskProcessInfo()
