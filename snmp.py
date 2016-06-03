#!/usr/bin/python
import itertools
import sys

import graphviz as gv
from easysnmp import Session
from netaddr import IPNetwork
from tabulate import tabulate

from interface import Interface
from network import Network
from routeEntry import RouteEntry
from router import Router

firstRouterIP = ""
COMMUNITY = ""
network = Network()  # crear objecte network


# RECULL LA TAULA DE RUTES A PARTIR D' UN ROUTER
def getRoutingTable(ipRouter, router=None):
    session = Session(hostname=ipRouter, community=COMMUNITY,
                      version=2)  # crear sessio per connectar amb el router
    networks = session.walk('IP-FORWARD-MIB::ipCidrRouteDest')  # xarxes desti
    nexthop = session.walk(
        'IP-FORWARD-MIB::ipCidrRouteNextHop')  # nexthop per la xarxa desti
    tipus = session.walk('IP-FORWARD-MIB::ipCidrRouteType')  # tipus de ruta
    masks = session.walk(
        'IP-FORWARD-MIB::ipCidrRouteMask')  # mascara de la xarxa desti

    table = list()

    for x, y, z, n in zip(networks, masks, nexthop,
                          tipus):  # combinem linea a linea la informacio rebuda
        route = RouteEntry(x.value, y.value,
                           z.value)  # creem un objecte ruta a partir de la informacio anterior
        router.addRoute(route)  # afegim aquesta ruta al router
        tipus = ''  # descodifiquem el valor rebut a llenguatge huma
        if (n.value == '1'):
            tipus = 'Other'
        elif (n.value == '2'):
            tipus = 'Reject'
        elif (n.value == '3'):
            tipus = 'Local'
        elif (n.value == '4'):
            tipus = 'Remote'

        table.append((x.value, y.value, z.value,
                      tipus))  # afegim la informacio anterior a la taula a mostrar

    print 'RoutingTable: '
    headers = ["Network", "Mask", "Nexthop", "Type"]  # definim capcalera taula
    print tabulate(table, headers, tablefmt="fancy_grid")  # printar taula


# A PARTIR DE LES MIPS RECULL TOTA LA INFORMACIO DE LES INTERFICIES D' UN ROUTER
def getRouterInterfaces(ipRouter, routerName=None):
    global network
    session = Session(hostname=ipRouter, community=COMMUNITY,
                      version=2)  # creem sessio a partir de la ip del router
    router = network.getRouter(
        routerName)  # recuperem objecte router a partir del nom
    ifaceIp = (
        session.walk('RFC1213-MIB::ipAdEntAddr'))  # recuperem llista d'ip

    table = list()

    # per cada ip...
    for ip in ifaceIp:
        ifaceIndex = (session.get(
            'RFC1213-MIB::ipAdEntIfIndex.' + ip.value))  # recuperem l' index que ocupa
        ifaceName = (session.get(
            'IF-MIB::ifDescr.' + ifaceIndex.value))  # a partir de l'index recuperem el nom de la
        ifaceMask = (session.get(
            'RFC1213-MIB::ipAdEntNetMask.' + ip.value))  # recuperem mascara a partir de la ip
        ifaceSpeed = (session.get(
            'IF-MIB::ifSpeed.' + ifaceIndex.value))  # en bits per second       #recuperem velocitat a partir de l'index
        ifaceCost = (session.get(
            'OSPF-MIB::ospfIfMetricValue.' + ip.value + '.0.0')).value  # recuperem el cost a partir de la ip

        speed = int(ifaceSpeed.value) / 1000000  # calculem velocitat en Mbps

        if ifaceCost == 'NOSUCHINSTANCE':  # apliquem valor per defecte en cas que no hagi especificat un cost
            ifaceCost = 'N/D'

        table.append((ifaceName.value, ip.value, ifaceMask.value, speed,
                      ifaceCost))  # afegim entrada a la taula a mostrar

        interface = Interface(ifaceName.value, ip.value, ifaceMask.value, speed,
                              ifaceCost)  # creem objecte interface amb tota la informacio necessaria
        router.addInterface(interface)  # afegim aquesta interficie al router
        network.addIP(ip.value, routerName,
                      ifaceMask.value)  # afegim la ip de la interficie a la llista de ips per calcular el path posteriorment

    print "Interfaces: "
    headers = ["Name", "IP", "Mask", "Speed(Mbps)", "Cost"]
    print tabulate(table, headers, tablefmt="fancy_grid")
    getRoutingTable(ipRouter,
                    router)  # continuem el proces d' obtencio d'informacio


# EXPLORA ROUTERS ADJACENTS PER INICIAR EL PROCES D' OBTENCIO D' INFORMACIO EN CADA UN RECURSIVAMENT
def getNeighbourAdress(ipRouter, lastRouter=None):
    global network
    session = Session(hostname=ipRouter, community=COMMUNITY, version=2)
    name = (session.get('SNMPv2-MIB::sysName.0'))  # recollim nom del router

    router = network.getRouter(
        name.value)  # recuperem objecte router en cas que existeixi...
    if router is None:
        router = Router(name.value)  # si no existeix l' inicialitzem

    if lastRouter is not None:  # si venim des d' un router...
        lastRouter.addAdjacentRouter(
            router)  # afegim l' adjacencia entre els routers que estem treballant

    if not network.routerExists(
            router):  # si a la xarxa no existeix el router actual...
        network.addRouter(router)  # afegim el router a l'objecte network
        print '\nROUTER NAME: ', router.getName()  # mostrem la seva informacio
        getRouterInterfaces(ipRouter, name.value)
        neighbours = (session.walk(
            'OSPF-MIB::ospfNbrIpAddr'))  # recuperem les IP dels adjacents i tornem a reproduir el proces per a cada un
        for x in neighbours:
            getNeighbourAdress(x.value,
                               router)  # crida recursiva a l' obtencio de la informacio


# GENERAR GRAF
def generateGraph():
    global network
    g1 = gv.Graph(format='svg', strict='yes')
    edgelist = list()

    for x in network.getRouters():  # per cada un dels routers...
        for y in x.getAdjacents():  # per cada un dels adjacents...
            head, tail = ipsSameNetwork(x,
                                        y)  # mirem si hi ha alguna interficie en comu entre aquests i recuperem les IPs i la seva velocitat
            g1.edge(str(x), str(y), headlabel=head,
                    taillabel=tail)  # afegim la interficie al graf

    g1.render('topology/topology.gv', view=True)  # renderitzem el graf


# RETORNA QUINES INTERFICIES SON LES QUE UNEIXEN DOS ROUTERS I LA SEVA VELOCITAT(rebem els dos routers a comparar)
def ipsSameNetwork(r1, r2):
    for x in r1.getInterfaces():  # per cada interficie del router1...
        ip1 = str(x.getIP())  # recuperem la ip
        mask1 = str(x.getMask())  # recuperem la mascara
        speed1 = str(x.getSpeed())  # recuperem la velocitat
        for y in r2.getInterfaces():  # per cada interficie del router2...
            ip2 = str(y.getIP())
            mask2 = str(y.getMask())
            speed2 = str(y.getSpeed())
            if IPNetwork(str(ip1 + '/' + mask1)) == IPNetwork(str(
                                    ip2 + '/' + mask2)):  # comparem la ip1+mascara1 amb ip2+mascara2 per saber si son les interficies que uneixen
                return ((ip1 + "\n" + speed1 + "Mbps"), (
                    ip2 + "\n" + speed2 + "Mbps"))  # en cas que coincideixi: retornem dos parametres: les ip de cada interficie i la seva velocitat


# CALCULAR RUTES ENTRE XARXES
def findBestRoutes():
    allIP = network.getIPs()
    # allIP[0] es IP
    # allIP[1] es nom del router a qui pertany
    # allIP[2] es la mascara de la ip

    table = list()
    # Permutem totes les ips de la xarxa per calcular la millor ruta entre elles
    for ipstart, ipend in itertools.permutations(allIP, 2):
        if ipstart[1] != ipend[1]:
            router = network.getRouter(ipstart[1])  # recuperem router
            nexthop = router.getNexthop(ipend[0], ipend[
                2])  # recuperem el nexhop a partir de la ip desti i la seva mascara
            toPrint = ipstart[0]  # incialitzem el path amb la ip inicial
            while (True):
                if (
                            nexthop == '0.0.0.0'):  # si el nexthop es 0.0.0.0 significa que hi estem directament connectats
                    toPrint += '-->' + ipend[
                        0]  # per tant afegim la ip desti al path
                    break
                else:  # sino...
                    router = network.getRouterbyIP(
                        nexthop)  # actualitzem el router a partir de la ip del nexthop
                    nexthop = router.getNexthop(ipend[0], ipend[
                        2])  # recalculem el nexthop per a la ip desti a partir del router actual
                    toPrint += '-->' + router.getName()  # afegim el router al path
            table.append((ipstart[0], ipend[0],
                          toPrint))  # afegim path a la taula per mostrar

    print "\n\nPATHS: "
    headers = ["From", "To", "Path"]
    print tabulate(table, headers, tablefmt="fancy_grid")


def main():
    global firstRouterIP
    global COMMUNITY
    if len(sys.argv) == 3:
        firstRouterIP = sys.argv[1]
        COMMUNITY = sys.argv[2]
    else:
        print "\nUSAGE: python snmp.py [ip] [community]\n"
        sys.exit()


if __name__ == "__main__":
    main()
    getNeighbourAdress(firstRouterIP)
    generateGraph()
    findBestRoutes()
