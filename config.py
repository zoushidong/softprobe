from utils import *
import constants
NETWORK_INTERFACE = "eno16777736"
SYSTEM_NAME = "sprobev0.99"
PLATFORM = getPlatform()

if PLATFORM == constants.PLATFORM_MAC : 
	NETWORK_INTERFACE = 'en5'

RECONNECTION_INTEVAL = 60

APPLICATION_PATH = getScriptPath()

PROCESS_LIST_PATH = getScriptPath()+'/processlist.json'

REMOTE_REPO_PATH = "sprobe@localhost:~/probe"

REMOTE_KEY_PATH = getScriptPath()+'/key/probe'
