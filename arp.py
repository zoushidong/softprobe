from __future__ import unicode_literals
import config
from constants import * 
import shlex
import subprocess
import os

"""
	return the arp info :
	{
		ip : '',
		mac : '',
		interface : ''
	}
"""
def parseArpInfo(line):
	cols = line.split(' ')
	info = {}
	info['ip'] = cols[1].replace('(','').replace(')','')
	info['mac'] = cols[3]
	if config.PLATFORM == PLATFORM_MAC : 
		info['interface'] = cols[5]
	elif config.PLATFORM == PLATFORM_UBUNTU : 
		info['interface'] = cols[-1]
	return info

def getArpInfo():
	pipe = subprocess.Popen(shlex.split('/usr/sbin/arp -a'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	stdoutdata,stderrordata = pipe.communicate()
	if stdoutdata : 
		lines = stdoutdata.split(os.linesep)
		arpInfos = [ parseArpInfo(line) for line in lines if line]
		return arpInfos
	return []

if __name__ == '__main__' : 
	print getArpInfo()
