from pysnmp.entity.rfc3413.oneliner import cmdgen

HOST_NAME='1.3.6.1.2.1.1.5.0'
CPU_IDLE='1.3.6.1.4.1.2021.11.11.0'
MEM_FREE='1.3.6.1.4.1.2021.4.11.0'
MEM_TOTAL='1.3.6.1.2.1.25.2.3.1.5'
MAC_ADDR='1.3.6.1.2.1.2.2.1.6'
IP_ADDR='1.3.6.1.2.1.4.20.1.1'
NEXT_HOP='1.3.6.1.2.1.4.21.1.7'
REQUEST=[HOST_NAME,CPU_IDLE,MEM_FREE,MEM_TOTAL,MAC_ADDR,IP_ADDR,NEXT_HOP]


def hostSysInfo(host='localhost',port=161,commity='wc'):
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
    cmdgen.CommunityData(commity),
    cmdgen.UdpTransportTarget((host, port)),
    NEXT_HOP
    )

    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                )
            )
        else:
            for varBindTableRow in varBindTable:
                for name, val in varBindTableRow:
                    print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))


    # errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
    # cmdgen.CommunityData(commity),
    # cmdgen.UdpTransportTarget((host, port)),
    # MEM_FREE
    # )

    # if errorIndication:
    #     print(errorIndication)
    # else:
    #     if errorStatus:
    #         print('%s at %s' % (
    #             errorStatus.prettyPrint(),
    #             errorIndex and varBinds[int(errorIndex)-1] or '?'
    #             )
    #         )
    #     else:
    #         for name, val in varBinds:
    #             print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

    # "cpuIdle":
    # {
    #     "oid":"1.3.6.1.4.1.2021.11.11.0",
    #     "type":"get",
    #     "re":"1[.]3[.]6[.]1[.]4[.]1[.]2021[.]11[.]11[.]0 = ([0-9]+[.]?[0-9]*)"
    # },
    # "memFree":
    # {
    #     "oid":"1.3.6.1.4.1.2021.4.11.0",
    #     "type":"get",
    #     "re":"1[.]3[.]6[.]1[.]4[.]1[.]2021[.]4[.]11[.]0 = ([0-9]+)"
    # },
    # "memTotal":
    # {
    #     "oid":"1.3.6.1.4.1.2021.4.5.0",
    #     "type":"get",
    #     "re":"1[.]3[.]6[.]1[.]4[.]1[.]2021[.]4[.]5[.]0 = ([0-9]+)"
    # },