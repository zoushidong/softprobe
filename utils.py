from __future__ import unicode_literals
import types 
import platform
from constants import * 
import os
import os.path

def ucfirst(content) : 
	if type(content) == types.StringType or type(content) == types.UnicodeType: 
		return content[0].upper() + content[1:]
	return None

def getPlatform():
	currentOs = platform.platform()
	if currentOs.find('Darwin')>=0:
		return PLATFORM_MAC
	elif currentOs.find('Ubuntu')>=0: 
		return PLATFORM_UBUNTU
	else : 
		return PLATFORM_UNKNOWN

def getMacAddressIndex():
	if getPlatform() == PLATFORM_MAC : 
		return 1
	return -1

def getScriptPath():
	return os.path.split(os.path.realpath(__file__))[0]


def parseArgs(args):
	args_parsed = []
	for arg in args : 
		print arg
		if arg['type'] == 'variable' : 
			arg = globals()[arg['value']]
			args_parsed.append(arg)
		else : 
			#TODO : other arg type
			pass
	return args_parsed
