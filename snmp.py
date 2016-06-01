#!/usr/bin/python
import sys
from easysnmp import Session
from easysnmp import snmp_get, snmp_set, snmp_walk
from interface import Interface
from router import Router
from network import Network
import graphviz as gv
from netaddr import IPNetwork
import itertools
from routeEntry import RouteEntry
from tabulate import tabulate

firstRouterIP = ""
COMMUNITY = "rocom"
network = Network()


def getRoutingTable(ipRouter,router = None):
    session = Session(hostname=ipRouter, community=COMMUNITY, version=2)
    networks = session.walk('IP-FORWARD-MIB::ipCidrRouteDest')
    nexthop = session.walk('IP-FORWARD-MIB::ipCidrRouteNextHop')
    tipus = session.walk('IP-FORWARD-MIB::ipCidrRouteType')
    masks = session.walk('IP-FORWARD-MIB::ipCidrRouteMask')

    table = list()


    for x, y, z, n in zip(networks, masks, nexthop, tipus):
        route = RouteEntry(x.value,y.value,z.value)
        router.addRoute(route)
        #print x.value, y.value, z.value, n.value
        tipus = ''
        if(n.value == '1'):
            tipus = 'Other'
        elif(n.value == '2'):
            tipus = 'Reject'
        elif(n.value == '3'):
            tipus = 'Local'
        elif(n.value == '4'):
            tipus = 'Remote'

        table.append((x.value, y.value, z.value, tipus))

    print 'RoutingTable: '
    headers = ["Network", "Mask", "Nexthop", "Type"]
    print tabulate(table, headers, tablefmt="fancy_grid")



def getRouterInterfaces(ipRouter, routerName=None):
    global network
    session = Session(hostname=ipRouter, community=COMMUNITY, version=2)

    router = network.getRouter(routerName)
    ifaceIp = (session.walk('RFC1213-MIB::ipAdEntAddr'))


    table = list()

    for ip in ifaceIp:
        ifaceIndex = (session.get('RFC1213-MIB::ipAdEntIfIndex.'+ip.value))
        ifaceName = (session.get('IF-MIB::ifDescr.'+ ifaceIndex.value))
        ifaceMask = (session.get('ipAdEntNetMask.'+ ip.value))
        ifaceSpeed = (session.get('ifSpeed.'+ifaceIndex.value))
        ifaceCost = (session.get('OSPF-MIB::ospfIfMetricValue.'+ip.value+'.0.0')).value

        if ifaceCost == 'NOSUCHINSTANCE':
            ifaceCost = 'N/D'

        #print ifaceName.value, ip.value, ifaceMask.value, ifaceSpeed.value, ifaceCost
        table.append((ifaceName.value, ip.value, ifaceMask.value, ifaceSpeed.value, ifaceCost))

        interface = Interface(ifaceName.value, ip.value, ifaceMask.value, ifaceSpeed.value, ifaceCost)  # falta el cost
        router.addInterface(interface)
        network.addIP(ip.value, routerName, ifaceMask.value)

    print "Interfaces: "
    headers = ["Name", "IP", "Mask", "Speed", "Cost"]
    print tabulate(table, headers, tablefmt="fancy_grid")
    getRoutingTable(ipRouter,router)



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
    #print("testing", r1, r1.getInterfaces(), r2, r2.getInterfaces())

    for x in r1.getInterfaces():
        ip1 = str(x.getIP())
        mask1 = str(x.getMask())
        for y in r2.getInterfaces():
            ip2 = str(y.getIP())
            mask2 = str(y.getMask())
            if IPNetwork(str(ip1 + '/' + mask1)) == IPNetwork(str(ip2 + '/' + mask2)):
                return (ip1, ip2)

def findBestRoutes():

    allIP = network.getIPs()
    #allIP[0] es IP
    #allIP[1] es nom del router a qui pertany
    #allIP[2] es la mascara de la ip

    table = list()

    for ipstart, ipend in itertools.permutations(allIP, 2):

        router = network.getRouter(ipstart[1])
        nexthop = router.getNexthop(ipend[0],ipend[2])
        toPrint = ipstart[0]
        while(True):
            if(nexthop == '0.0.0.0'):
                toPrint += '-->' + ipend[0]
                break
            else:
                router = network.getRouterbyIP(nexthop)
                nexthop = router.getNexthop(ipend[0],ipend[2])
                toPrint += '-->' + router.getName()
        table.append((ipstart[0],ipend[0],toPrint))


    print "\n\nPATHS: "
    headers = ["From", "To", "Path"]
    print tabulate(table, headers, tablefmt="fancy_grid")
        #print toPrint




if __name__ == "__main__":
    main()
    getNeighbourAdress(firstRouterIP)
    generateGraph()
    #network.printRouters()
    findBestRoutes()
