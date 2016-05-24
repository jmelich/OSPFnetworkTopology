class Interface:
    def __init__(self,name):
        self.name=""
        self.ipAddress=""
        self.netmask=""
        self.speed = 0
        self.cost=0

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
