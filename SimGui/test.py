''' Testing the centralised link scheduling '''

'''Muhumuza Joshua josh.jesusreigns@gmail.com'''
'''Kasumba robert robein@ymail.com'''
'''Mary Nsabagwa marynsabagwa@gmail.com'''


from Link import Link

from SimEngine import SimEngine, \
                      SimSettings, \
                      Mote


TIMESLOTS,FREQUENCIES =100,16
SlotFrame=[[None for ts in range(TIMESLOTS)] for ts in range(FREQUENCIES)]

class Test(object):

    def __init__(self):

        #self.engine  = SimEngine.SimEngine()
        # variables

        self.schedules  = {}
        self.linksavailable ={}



    '''def returnLinks(self):
        for mote in self.engine.motes:
            for (neighbor) in mote.getTxCells():
                self.linksavailable[(mote,neighbor)] = (mote,neighbor)

        return self.linksavailable'''


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
        singleSlot=[row[timeSlot] for row in  SlotFrame]
        if any(x==link for x in singleSlot):
            return True
        for link1 in singleSlot:
            if link1==None:
                continue
            if not link.isCompartible(link1):
                return True
        return False

    def schedule(self,linksList):
        #SlotFrame=[[None for ts in range(TIMESLOTS)] for ts in range(FREQUENCIES)]
        for i in range(FREQUENCIES):
            for j in range(TIMESLOTS):
                SlotFrame[i][j] = None
        linksList = self.generateCompartibleLinks(linksList)
        linksListCopy = linksList[:]

        while(len(linksListCopy)>0):
            cur_link = self.chooseNextLink(linksListCopy)
            linkassigned = False
            channelOffset,timeSlot =0,0
            while(timeSlot<TIMESLOTS):
                if channelOffset==FREQUENCIES:
                    timeSlot+=1
                    channelOffset=0
                if not SlotFrame[channelOffset][timeSlot] == None:
                    channelOffset+=1
                    continue
                if not self.isConstraints(cur_link,timeSlot):
                    SlotFrame[channelOffset][timeSlot]=cur_link
                    linkassigned =True
                    break
                else:
                    timeSlot+=1
                    channelOffset=0
                    continue
            cur_link.reduceTimeToSchedule()
            if cur_link.timesToSchedule==0:
                del linksListCopy[linksListCopy.index(cur_link)]
        return SlotFrame
### for testing purposes









#displaying the slotFrame
'''for i in range(FREQUENCIES):
    for j in range(TIMESLOTS):
        if not SlotFrame[i][j] == None:
           print ""+ str(SlotFrame[i][j].getId()) +" ",
        else:
            print "None ",
    print ""
'''
