# -*- coding: utf-8 -*-
import os
import json
from utils import * 

import subprocess
import constants

def operate_conn(pipe=None):
	f = open('rebooter.config.json','r+')
	conf = json.load(f)
	if conf['need_reboot'] : 
		f.close()
		conf['need_reboot'] = False
		f = open('rebooter.config.json','w')
		json.dump(conf,f)
		f.close
		subprocess.Popen(['sudo','reboot'])

if __name__ == '__main__' : 
	operate_conn()
	