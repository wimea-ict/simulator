''' this file defines the structure of a link
A link has a sender and receiver node, the number of times its scheduled plus methods of
its behaviour
'''

class Link(object):
    def __init__(self,node,timesToschedule, id):
        self.compartibleLinks = []
        self.sendNode=node[0]
        self.rcvNode = node[1]
        self.timesToSchedule=timesToschedule
        self.isScheduled = False
        self.timesScheduledAlready =0
        self.packetsToCarry=timesToschedule
        self.id = id

    def reduceTimeToSchedule(self):
        self.timesToSchedule -=1
        self.timesScheduledAlready+=1
        if  self.timesToSchedule<=0:
             self.timesToSchedule=0

    def needsToschedule(self):
        if  self.timesToSchedule==0:
            return False
        else:
            return True
    def addCompartibleLink(self,link):
        self.compartibleLinks.append(link)
    def isCompartible(self,link):
        return any(l == link for l in self.compartibleLinks);
        #if the link is not found in the set.
        return False;
    def sharesNode(self,link):
        return (self.sendNode==link.sendNode or self.rcvNode==link.rcvNode or self.rcvNode==link.sendNode or self.sendNode==link.rcvNode)
    def getLinkInfo(self):
        return  self.sendNode+"->"+self.rcvNode

    def getId(self):
        return self.id
