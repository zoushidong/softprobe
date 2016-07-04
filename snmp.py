from pysnmp.entity.rfc3413.oneliner import cmdgen
import json
import os
import unicodedata
import re

def hostSysInfo(host='localhost',port=161,commity='sprobe'):
	getOids = []
	walkOids = []
	res = {}
	result = {}
	response = ''
	oidSet = json.load(open(os.path.join(os.path.dirname(__file__),'oid.json'),"r+"))
	for oidname in oidSet:
		oid = oidSet.get(oidname)
		if oid.get("type") == 'get':
			getOids.append(unicodedata.normalize('NFKD', oid.get("oid")).encode('ascii','ignore'))
		else:
			walkOids.append(unicodedata.normalize('NFKD', oid.get("oid")).encode('ascii','ignore'))
		res[oidname] = oid.get("re")
		result[oidname] = ''
	# print walkOids
	# print getOids
	result["status"] = "success"
	cmdGen = cmdgen.CommandGenerator()
	errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
	cmdgen.CommunityData(commity),
	cmdgen.UdpTransportTarget((host, port),timeout=1, retries=0),
	*walkOids
	)
	if errorIndication:
	    print("walkError: " + str(errorIndication))
	    result["status"] = "fail"
	    return result
	else:
	    if errorStatus:
	        print('walkError: ' + '%s at %s' % (
	            errorStatus.prettyPrint(),
	            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
	            )
	        )
	        result["status"] = "fail"
	        return result
	    else:
	        for varBindTableRow in varBindTable:
	            for name, val in varBindTableRow:
	                response +=name.prettyPrint() + " = " + val.prettyPrint() + '\n'

	errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
	cmdgen.CommunityData(commity),
	cmdgen.UdpTransportTarget((host, port),timeout=1, retries=0),
	*getOids
	)

	if errorIndication:
	    print("getError: " + str(errorIndication))
	    result["status"] = "fail"
	    return result
	else:
	    if errorStatus:
	        print('getError: ' + '%s at %s' % (
	            errorStatus.prettyPrint(),
	            errorIndex and varBinds[int(errorIndex)-1] or '?'
	            )
	        )
	        result["status"] = "fail"
	        return result
	    else:
	        for name, val in varBinds:
	            response +=name.prettyPrint() + " = " + val.prettyPrint() + '\n'

	# print response
	for name in res:
		pattern = res.get(name)
		matchResult = re.findall(pattern,response,re.M|re.I)
		if matchResult:
			result[name] = matchResult
		# else:
		# 	result[name] = None

	return resultOperate(result)

def resultOperate(result):
	if 'cpuIdle' in result:
		if result.get('cpuIdle'):
			cpuPersent = 100 - int(result.get('cpuIdle')[0])
		else:
			cpuPersent = None
		del result['cpuIdle']
		result['cpuPersent'] = cpuPersent
	if 'memFree' and 'memTotal' in result:
		if result.get('memFree') and result.get('memTotal'):
			memPersent = round((int(result.get('memTotal')[0]) - int(result.get('memFree')[0])) *100 / float(result.get('memTotal')[0]))
		else:
			memPersent = None
		del result['memFree'], result['memTotal']
		result['memPersent'] = memPersent

	return result


# print hostSysInfo()
