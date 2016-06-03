from netaddr import IPNetwork


# CLASSE QUE REPRESENTA UN OBJECTE ROUTER AMB ELS SEUS ATRIBUTS I METODES
class Router:
    def __init__(self, name):
        self.name = name
        self.interfaces = list()
        self.adjacents = list()
        self.routeTable = list()

    def getName(self):
        return self.name

    def addInterface(self, interface):
        self.interfaces.append(interface)

    def getInterfaces(self):
        return self.interfaces

    def getAdjacents(self):
        return self.adjacents

    def addRoute(self, route):
        self.routeTable.append(route)

    def getRoutingTable(self):
        return self.routeTable

    # comparem la ip+mascara desti amb les entrades de la taula d' enrutament per retornar el nexthop
    def getNexthop(self, ip, mask):
        for route in self.routeTable:
            if IPNetwork(str(ip + '/' + mask)) == IPNetwork(
                    str(route.getNetwork() + '/' + route.getMask())):
                return route.getNexthop()

    # afegim router als adjacents en cas que no hi sigui
    def addAdjacentRouter(self, router):
        if router not in self.adjacents:
            self.adjacents.append(router)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
