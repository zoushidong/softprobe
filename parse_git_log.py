# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import chardet
import json
import sys
import os
import os.path
import codecs
import subprocess
import shlex

def getScriptPath():
	return os.path.split(os.path.realpath(__file__))[0]

def parseGitLog(content):
	commits = []
	commit = {}
	content_start = False 
	commit_content = ''
	for line in content : 
		encode = chardet.detect(line)['encoding']
		if encode != 'ascii' : 
			line = unicode(line,encode)
			line = line.replace(u'\n',u'')
		else : 
			line = line.replace('\n','')
		if line.find('commit') == 0 : 
			commit['commit_id'] = line.split(' ')[1]
		elif line.find('Author') == 0 : 
			author_info =  line.split(':')[1].strip()
			commit['author'] = author_info.split(' ')[0]
			commit['email'] = author_info.split(' ')[1].replace('<','').replace('>','')
		elif line.find('Date') == 0 : 
			commit['date'] = line.split(':')[1].strip()
		else :
			if not line : 
				if not content_start: 
					content_start = True
				else :
					if not commit_content : 
						continue
					commit['content'] = commit_content
					commits.append(commit)
					commit = {}
					commit_content = ''
					content_start = False
			else : 
				commit_content = commit_content+line.strip()+"\n"
	return commits[::-1]


if __name__ == '__main__' : 
	os.chdir(getScriptPath())
	print 'current dir is ',os.getcwd()
	process = subprocess.Popen(shlex.split('git log'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	process.wait()
	log = process.stdout
	with codecs.open(os.path.dirname(getScriptPath())+'/commits.json','w+','utf-8') as output : 
		json.dump(parseGitLog(log),output,ensure_ascii=False,indent=4)
	


