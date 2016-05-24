from router import Router
from interface import Interface

class Network():
    def __init__(self):
        self.routers = list()

    def addRouter(self, router):
        if not self.routerExists(router):
            self.routers.append(router)

    def routerExists(self,router):
        for x in self.routers:
            if x.getName() == router.getName():
                return True
        return False

    def printRouters(self):
        for x in self.routers:
            print 'ROUTER',x, 'adjacents:'
            for y in x.getAdjacents():
                print y

    def getRouter(self,name):
        for x in self.routers:
            if x.getName() == name:
                return x
        return None

    def getRouterByPos(self,pos):
        return self.routers[0]

    def getRouters(self):
        return self.routers
