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
            print x
