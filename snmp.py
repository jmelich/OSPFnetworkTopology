#!/usr/bin/python
import sys
from easysnmp import Session
from easysnmp import snmp_get, snmp_set, snmp_walk
from interface import Interface
from router import Router
from network import Network




firstRouterIP = ""
COMMUNITY= "rocom"

network = Network()






def main():
    global firstRouterIP
    if len(sys.argv) == 2:
        firstRouterIP = sys.argv[1]
    else:
        firstRouterIP = "11.0.0.1"
        #print "funcionament: python snmp.py <ip>"

def getRouterInterfaces():
    session = Session(hostname=firstRouterIP, community=COMMUNITY, version=2)
    #location = (session.get(MYMIPS.ROUTERNAME)).value
    ifaceNames = (session.walk('ifDescr'))
    ifaceIp = (session.walk('ipAdEntAddr'))
    masks = (session.walk('ipAdEntNetMask'))
    speed = (session.walk('ifSpeed'))
    for x,y,m,s in zip(ifaceNames, ifaceIp,masks,speed):
        print x.value, y.value, m.value, s.value

    #print location

def getNeighbourAdress(ipRouter):
    global network
    session = Session(hostname=ipRouter, community=COMMUNITY, version=2)
    name = (session.get('SNMPv2-MIB::sysName.0'))

    router = Router(name.value)

    if not network.routerExists(router):
        print 'adding router:', router.getName()
        network.addRouter(router)
        neighbours = (session.walk('OSPF-MIB::ospfNbrIpAddr'))
        for x in neighbours:
            getNeighbourAdress(x.value)


def getLocation():
    session = Session(hostname=firstRouterIP, community=COMMUNITY, version=2)

    location = session.get('sysLocation.0').value
    print location




if __name__ == "__main__":
    main()
    #initializeRouterList()
    getRouterInterfaces()
    getNeighbourAdress(firstRouterIP)
    network.printRouters()
    #getLocation()
