from router import Router
from interface import Interface


class Network():

    def __init__(self):
        self.routers = list()
        self.allIPs = list()

    def addRouter(self, router):
        if not self.routerExists(router):
            self.routers.append(router)

    def routerExists(self, router):
        for x in self.routers:
            if x.getName() == router.getName():
                return True
        return False

    def printRouters(self):
        for x in self.routers:
            print 'ROUTER', x, 'adjacents:'
            for y in x.getAdjacents():
                print y

    def getRouter(self, name):
        for x in self.routers:
            if x.getName() == name:
                return x
        return None

    def getIPs(self):
        return self.allIPs

    def addIP(self,ip,mask, router):
        for x in self.allIPs:
            if x[0] == ip and x[1] == mask and x[2] == router:
                return None
        value=[ip,mask,router]
        self.allIPs.append(value)

    def getRouterbyIP(self,ip):
        for x in self.allIPs:
            if x[0] == ip:
                return self.getRouter(x[1])

    def getRouterByPos(self, pos):
        return self.routers[0]

    def getRouters(self):
        return self.routers
