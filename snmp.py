#!/usr/bin/python
import sys
from easysnmp import Session
from easysnmp import snmp_get, snmp_set, snmp_walk
from interface import Interface
from router import Router
from network import Network
import graphviz as gv
from netaddr import IPNetwork

firstRouterIP = ""
COMMUNITY = "rocom"
network = Network()


def getRoutingTable(ipRouter):
    session = Session(hostname=ipRouter, community=COMMUNITY, version=2)
    networks = session.walk('IP-FORWARD-MIB::ipCidrRouteDest')
    nexthop = session.walk('IP-FORWARD-MIB::ipCidrRouteNextHop')
    tipus = session.walk('IP-FORWARD-MIB::ipCidrRouteType')
    masks = session.walk('IP-FORWARD-MIB::ipCidrRouteMask')

    print 'RoutingTable: '
    for x, y, z, n in zip(networks, masks, nexthop, tipus):
        print x.value, y.value, z.value, n.value


def getRouterInterfaces(ipRouter, routerName=None):
    session = Session(hostname=ipRouter, community=COMMUNITY, version=2)

    router = network.getRouter(routerName)
    ifaceNames = (session.walk('ifDescr'))
    ifaceIp = (session.walk('ipAdEntAddr'))
    masks = (session.walk('ipAdEntNetMask'))
    speed = (session.walk('ifSpeed'))

    print 'InterfacesInfo: '
    for x, y, m, s in zip(ifaceNames, ifaceIp, masks, speed):
        interface = Interface(x.value, y.value, m.value, s.value)  # falta el cost
        router.addInterface(interface)
        print x.value, y.value, m.value, s.value

    getRoutingTable(ipRouter)
    # print location


# explora routers adjacents i crida getRouterInterfaces()per mostrar la info de les interficies
def getNeighbourAdress(ipRouter, lastRouter=None):
    global network
    session = Session(hostname=ipRouter, community=COMMUNITY, version=2)
    name = (session.get('SNMPv2-MIB::sysName.0'))

    router = network.getRouter(name.value)
    if router is None:
        router = Router(name.value)
    if lastRouter is not None:
        lastRouter.addAdjacentRouter(router)

    if not network.routerExists(router):
        # print 'adding router:', router.getName()
        network.addRouter(router)
        print '\nROUTER NAME: ', router.getName()
        getRouterInterfaces(ipRouter, name.value)
        neighbours = (session.walk('OSPF-MIB::ospfNbrIpAddr'))
        for x in neighbours:
            getNeighbourAdress(x.value, router)


def main():
    global firstRouterIP
    if len(sys.argv) == 2:
        firstRouterIP = sys.argv[1]
    else:
        firstRouterIP = "11.0.0.1"
        # print "funcionament: python snmp.py <ip>"


def generateGraph():
    global network
    g1 = gv.Graph(format='svg', strict='yes')
    edgelist = list()

    for x in network.getRouters():
        for y in x.getAdjacents():
            head, tail = ipsSameNetwork(x, y)
            g1.edge(str(x), str(y), headlabel=head, taillabel=tail)

    g1.render('test-output/round-table.gv', view=True)


def ipsSameNetwork(r1, r2):
    # router1 = network.getRouter(r1)
    # router2 = network.getRouter(r2)
    # print r1.getInterfaces()
    print("testing", r1, r1.getInterfaces(), r2, r2.getInterfaces())

    for x in r1.getInterfaces():
        ip1 = str(x.getIP())
        mask1 = str(x.getMask())
        for y in r2.getInterfaces():
            ip2 = str(y.getIP())
            mask2 = str(y.getMask())
            if IPNetwork(str(ip1 + '/' + mask1)) == IPNetwork(str(ip2 + '/' + mask2)):
                return (ip1, ip2)


if __name__ == "__main__":
    main()
    getNeighbourAdress(firstRouterIP)
    generateGraph()
    network.printRouters()
