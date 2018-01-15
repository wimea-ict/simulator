''' Testing the centralised link scheduling '''

'''Muhumuza Joshua josh.jesusreigns@gmail.com'''
'''Kasumba robert robein@ymail.com'''
'''Mary Nsabagwa marynsabagwa@gmail.com'''


from Link import Link

import SimSettings
import SimEngine


import Mote
import random



class Scheduler(object):
    def __init__(self):
        self.setting = SimSettings.SimSettings()
        self.schedules  = {}
        self.linksavailable ={}
        self.links           = []
        self.linksnow        = []
        self.linksrequired   = []
        self.linksList       = []
        self.slotFrameSize   = 1
        self.timeslots       = self.setting.slotframeLength
        self. channels =self.setting.numChans
        self.slotFrame = [[None for ts in range(self.timeslots)] for ts in range(self.channels)]

    def generateCompartibleLinks(self,linksList):
        count =0
        updatedList =[]

        for link1 in linksList:
            for link2 in linksList:

                if not link1.sharesNode(link2):
                    link1.addCompartibleLink(link2)
        return linksList
    def chooseNextLink(self,linksList):
        #sort in descending order based on timesToSchedule and timesScheduledAlready
        linksList.sort(key=lambda x:(x.timesToSchedule,-x.timesScheduledAlready),reverse=True)
        return linksList[0]

    def isConstraints(self,link,timeSlot):
        #checks if the assignment link to the passed timeSlot fails dues to any constraint
        singleSlot=[row[timeSlot] for row in  self.slotFrame]
        if any(x==link for x in singleSlot):
            return True
        for link1 in singleSlot:
            if link1==None:
                continue
            if not link.isCompartible(link1):
                return True
        return False

    def schedule(self,linksList):
        #SlotFrame=[[None for ts in range(timeslots)] for ts in range(channels)]
        for i in range(self.channels):
            for j in range(self.timeslots):
                self.slotFrame[i][j] = None
        linksList = self.generateCompartibleLinks(linksList)
        linksListCopy = linksList[:]
        while(len(linksListCopy)>0):
            cur_link = self.chooseNextLink(linksListCopy)
            linkassigned = False
            channelOffset,timeSlot =0,0
            while(timeSlot<self.timeslots):
                if channelOffset==self.channels:
                    timeSlot+=1
                    channelOffset=0
                if not self.slotFrame[channelOffset][timeSlot] == None:
                    channelOffset+=1
                    continue
                if not self.isConstraints(cur_link,timeSlot):
                    self.slotFrame[channelOffset][timeSlot]=cur_link
                    linkassigned =True
                    break
                else:
                    timeSlot+=1
                    channelOffset=0
                    continue
            cur_link.reduceTimeToSchedule()
            if cur_link.timesToSchedule==0:
                del linksListCopy[linksListCopy.index(cur_link)]
        #Randomise channels assigned to each links
        linksdict ={}
        for ts in range(self.timeslots):
            for j in range(self.channels):
                key = random.randint(0,self.channels-1)
                while linksdict.has_key(key):
                    key = random.randint(0,self.channels-1)
                linksdict[key] =self.slotFrame[j][ts]
            for j in range(self.channels):
                self.slotFrame[j][ts]=None
            for key, value in linksdict.items():

                self.slotFrame[key][ts]=value
            linksdict.clear()
        return self.slotFrame

    def createLinks(self):
        self.links=[]
	#establishing how many packets each mote has to send in a single slot frame
	motes = sorted(self.engine.motes, key=lambda mote: mote.getMoteRank(),reverse=True)
        for mote in motes:
            neighbors =mote._myNeigbors()
            if neighbors:
                parent=sorted(neighbors, key=lambda mote: mote.getMoteRank())[0]
                if not parent.id==0:
                    parent._increasePacketsToSend(mote.packetsTosend)
	#creating links. Each mote creates a link with it's parent ie the neighbor with the closest rank
        for mote in self.engine.motes:
            neighbors =mote._myNeigbors()
            if neighbors:
                parent=sorted(neighbors, key=lambda mote: mote.getMoteRank())[0]
		#each link consists of the sender mote, receiver(parent) and the number of packets to send
                self.links.append(tuple([tuple([mote.id,parent.id]),mote.packetsTosend]))
        return self.links

    def createLinksList(self):
        linkcounter =1
        self.createLinks()
        for (m,n) in self.links:
            a = Link(m,n,linkcounter)
            linkcounter+=1
            self.linksList.append(a)
        return self.linksList

    def updateMoteSchedules(self):
        motes_timeslot={}
        linksList = [m for m in self.createLinksList()]
        slotFrame =self.schedule(linksList)
        for i in range(self.channels):
            for j in range(self.timeslots):
                link=slotFrame[i][j]
                if link == None:
                    continue
                else:
                    if not motes_timeslot.has_key(link.sendNode):
                        motes_timeslot[link.sendNode]=[(j,self.engine.motes[0].DIR_TX,link.rcvNode,i)]
                    else:
                        motes_timeslot[link.sendNode].append((j,self.engine.motes[0].DIR_TX,link.rcvNode,i))
                    if not motes_timeslot.has_key(link.rcvNode):
                        motes_timeslot[link.rcvNode]=[(j,self.engine.motes[0].DIR_RX,link.sendNode,i)]
                    else:
                        motes_timeslot[link.rcvNode].append((j,self.engine.motes[0].DIR_RX,link.sendNode,i))
                    if (j+1)>self.slotFrameSize:
                        self.slotFrameSize=(j+1)
        #double the slot frame to create free time slots
        self.slotFrameSize = self.setting.slotframeLength
        for mote in self.engine.motes:
            if motes_timeslot.has_key(mote.id):
                mote.assignSchedule(motes_timeslot[mote.id],self.slotFrameSize)

    def getUpdatePeriod(self):
        return 10000



    @property
    def engine(self):
        return SimEngine.SimEngine(failIfNotInit=True)

    @property
    def settings(self):
        return SimSettings.SimSettings(failIfNotInit=True)
