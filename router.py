from interface import Interface


class Router:

    def __init__(self, name):
        self.name = name
        self.interfaces = list()
        self.adjacents = list()

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

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
