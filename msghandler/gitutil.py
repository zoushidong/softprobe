import sys,os
import shlex
import subprocess
import types
import os.path
import config
'''
import pygit2
from pygit2 import * 

def credentials(self, url, username_from_url, allowed_types):
	pri_dir = sys.path[0]+'/key/probe'
	pub_dir = sys.path[0]+'/key/probe.pub'
	return Keypair(username_from_url,pub_dir,pri_dir,'')

def getRepository(path):
	repoPath = discover_repository(path)
	if repoPath : 
		return Repository(repoPath)
	else : 
		return None

def repo(func):
	def inner(*args,**kargs):
		if not len(args) : 
			return
		if isinstance(args[0],str) or isinstance(args,unicode) : 
			args = list(args)
			args[0] = getRepository(args[0])
			if args[0] : 
				args = tuple(args)
				return func(*args,**kargs)
			else:
				print "Invalid repo path"
		else : 
			return func(*args,**kargs)
	return inner

@repo
def getCurrentVersion(repo):
	return repo.head.target

@repo
def revert(repo):
	"""
	revert to last commit
	"""
	versions = getVersionList(repo)
	pre_commit_id = None
	for idx in xrange(len(versions)) : 
		if versions[idx].id == repo.head.target and idx!=0: 
			pre_commit_id = versions[idx-1].id
			break
	if pre_commit_id : 
		repo.reset(pre_commit_id,GIT_RESET_HARD)
	else : 
		print "You are in first version of this repo"

def pull(repo, remote_name='origin'):
    for remote in repo.remotes:
    	remote.credentials = types.MethodType(credentials,remote)
        if remote.name == remote_name:
            remote.fetch()
            remote_master_id = repo.lookup_reference('refs/remotes/origin/master').target
            merge_result, _ = repo.merge_analysis(remote_master_id)
            # Up to date, do nothing
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                return
            # We can just fastforward
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                master_ref = repo.lookup_reference('refs/heads/master')
                master_ref.set_target(remote_master_id)
                # Terrible hack to fix set_target() screwing with the index
                repo.reset(master_ref.target, pygit2.GIT_RESET_HARD)
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                repo.merge(remote_master_id)
                print repo.index.conflicts

                assert repo.index.conflicts is None, 'Conflicts, ahhhh!'
                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD',
                                            user,
                                            user,
                                            'Merge!',
                                            tree,
                                            [repo.head.target, remote_master_id])
                repo.state_cleanup()
            else:
                raise AssertionError('Unknown merge analysis result')



@repo
def changeToVersion(repo,oid):
	repo.reset(oid,GIT_RESET_HARD)

@repo
def getVersionList(repo):
	"""
		return the list of commit object 
	"""
	all_commits = [str(x.id) for x in repo.walk(repo.head.target,GIT_SORT_TIME)]
	return all_commits[::-1]
'''


def updateToLatestVersion(repo=config.APPLICATION_PATH):
	if scp(config.REMOTE_REPO_PATH,repo,config.REMOTE_KEY_PATH) : 
		return True
	raise Exception("SCP ERROR !")

def scp(remote,dest,keypath) : 
	dirname = os.path.dirname(dest)
	cmd = "scp -i %s -r %s %s"%(keypath,remote,dirname)
	cmd = shlex.split(cmd)
	sub = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	returncode = sub.wait()
	if returncode !=0: 
		return False
	return True

def reboot():
        cmd = "sudo reboot"
        cmd = shlex.split(cmd)
        sub = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        returncode = sub.wait()
        if returncode != 0:
                return False
        return True
		
def reverseSSH(port,server,keypath,user='root'):
        cmd = "ssh -NfR %s:localhost:22 %s@%s -i %s"%(port,user,server,keypath)
        cmd = shlex.split(cmd)
        sub = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        returncode = sub.wait()
        if returncode != 0:
                return False
        return True

def killReverseSSH():
        #cmd = "ps -ef | grep 'ssh -NfR' | awk '{print $2}' | xargs kill -9"
        sub1 = subprocess.Popen(shlex.split('ps -ef'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        sub2 = subprocess.Popen(shlex.split("grep 'ssh -NfR'"),stdin=sub1.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        sub3 = subprocess.Popen(shlex.split("awk '{print $2}'"),stdin=sub2.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        sub4 = subprocess.Popen(shlex.split('xargs kill -9'),stdin=sub3.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdoutdata,stderrordata = sub4.communicate()
        returncode = sub4.wait()
        if returncode != 0:
                return False
        return True
