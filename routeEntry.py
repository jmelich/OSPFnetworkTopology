
class RouteEntry():
    def __init__(self,network,mask,nexthop):
        self.network = network
        self.mask = mask
        self.nexthop = nexthop

    def getNetwork(self):
        return self.network

    def getMask(self):
        return self.mask

    def getNexthop(self):
        return self.nexthop
