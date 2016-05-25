from interface import Interface
from netaddr import IPNetwork

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

    def addAdjacentRouter(self, router):
        if router not in self.adjacents:
            self.adjacents.append(router)

    def getInterfaces(self):
        return self.interfaces

    def getAdjacents(self):
        return self.adjacents

    def addRoute(self,route):
        self.routeTable.append(route)

    def getRoutingTable(self):
        return self.routeTable

    def getNexthop(self, ip, mask):
        for route in self.routeTable:
            if IPNetwork(str(ip + '/' + mask)) == IPNetwork(str(route.getNetwork() + '/' + route.getMask())):
                return route.getNexthop()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
