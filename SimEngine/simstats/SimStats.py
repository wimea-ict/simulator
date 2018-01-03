#!/usr/bin/python
'''
\brief Collects and logs statistics about the ongoing simulation.

\author Thomas Watteyne <watteyne@eecs.berkeley.edu>
\author Kazushi Muraoka <k-muraoka@eecs.berkeley.edu>
\author Nicola Accettura <nicola.accettura@eecs.berkeley.edu>
\author Xavier Vilajosana <xvilajosana@eecs.berkeley.edu>
'''

#============================ logging =========================================

import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log = logging.getLogger('SimStats')
log.setLevel(logging.ERROR)
log.addHandler(NullHandler())

#============================ imports =========================================

import SimEngine
import SimSettings

#============================ defines =========================================

#============================ body ============================================

class SimStats(object):

    #===== start singleton
    _instance      = None
    _init          = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SimStats,cls).__new__(cls, *args, **kwargs)
        return cls._instance
    #===== end singleton

    def __init__(self,runNum):

        #===== start singleton
        if self._init:
            return
        self._init = True
        #===== end singleton

        # store params
        self.runNum                         = runNum

        # local variables
        self.engine                         = SimEngine.SimEngine()
        self.settings                       = SimSettings.SimSettings()

        # stats
        self.stats                          = {}
        self.columnNames                    = []

        # start file
        if self.runNum==0:
            self._fileWriteHeader()

        # schedule actions
        self.engine.scheduleAtStart(
            cb          = self._actionStart,
        )
        self.engine.scheduleAtAsn(
            asn         = self.engine.getAsn()+self.settings.slotframeLength-1,
            cb          = self._actionEndCycle,
            uniqueTag   = (None,'_actionEndCycle'),
            priority    = 10,
        )
        self.engine.scheduleAtEnd(
            cb          = self._actionEnd,
        )

    def destroy(self):
        # destroy my own instance
        self._instance                      = None
        self._init                          = False

    #======================== private =========================================

    def _actionStart(self):
        '''Called once at beginning of the simulation.'''
        pass

    def _actionEndCycle(self):
        '''Called at each end of cycle.'''

        cycle = int(self.engine.getAsn()/self.settings.slotframeLength)

        # print
        if self.settings.cpuID==None:
            print('   cycle: {0}/{1}'.format(cycle,self.settings.numCyclesPerRun-1))

        # write statistics to output file
        self._fileWriteStats(
            dict(
                {
                    'runNum':              self.runNum,
                    'cycle':               cycle,
                }.items() +
                self._collectSumMoteStats().items()  +
                self._collectScheduleStats().items()
            )
        )

        # schedule next statistics collection
        self.engine.scheduleAtAsn(
            asn         = self.engine.getAsn()+self.settings.slotframeLength,
            cb          = self._actionEndCycle,
            uniqueTag   = (None,'_actionEndCycle'),
            priority    = 10,
        )

    def _actionEnd(self):
        '''Called once at end of the simulation.'''
        self._fileWriteTopology()

    #=== collecting statistics

    def _collectSumMoteStats(self):
        returnVal = {}

        for mote in self.engine.motes:
            moteStats        = mote.getMoteStats()
            if not returnVal:
                returnVal    = moteStats
            else:
                for k in returnVal.keys():
                    returnVal[k] += moteStats[k]

        return returnVal

    def _collectScheduleStats(self):

        # compute the number of schedule collisions

        # Note that this cannot count past schedule collisions which have been relocated by 6top
        # as this is called at the end of cycle
        scheduleCollisions = 0
        txCells = []
        for mote in self.engine.motes:
            for (ts,cell) in mote.schedule.items():
                (ts,ch) = (ts,cell['ch'])
                if cell['dir']==mote.DIR_TX:
                    if (ts,ch) in txCells:
                        scheduleCollisions += 1
                    else:
                        txCells += [(ts,ch)]

        # collect collided links
        txLinks = {}
        for mote in self.engine.motes:
            for (ts,cell) in mote.schedule.items():
                if cell['dir']==mote.DIR_TX:
                    (ts,ch) = (ts,cell['ch'])
                    (tx,rx) = (mote,cell['neighbor'])
                    if (ts,ch) in txLinks:
                        txLinks[(ts,ch)] += [(tx,rx)]
                    else:
                        txLinks[(ts,ch)]  = [(tx,rx)]

        collidedLinks = [txLinks[(ts,ch)] for (ts,ch) in txLinks if len(txLinks[(ts,ch)])>=2]

        # compute the number of Tx in schedule collision cells
        collidedTxs = 0
        for links in collidedLinks:
            collidedTxs += len(links)

        # compute the number of effective collided Tx
        effectiveCollidedTxs = 0
        insufficientLength   = 0
        for links in collidedLinks:
            for (tx1,rx1) in links:
                for (tx2,rx2) in links:
                    if tx1!=tx2 and rx1!=rx2:
                        # check whether interference from tx1 to rx2 is effective
                        if tx1.getRSSI(rx2) > rx2.minRssi:
                            effectiveCollidedTxs += 1


        return {'scheduleCollisions':scheduleCollisions, 'collidedTxs': collidedTxs, 'effectiveCollidedTxs': effectiveCollidedTxs}

    #=== writing to file

    def _fileWriteHeader(self):
        output          = []
        output         += ['## {0} = {1}'.format(k,v) for (k,v) in self.settings.__dict__.items() if not k.startswith('_')]
        output         += ['\n']
        output          = '\n'.join(output)

        with open(self.settings.getOutputFile(),'w') as f:
            f.write(output)

    def _fileWriteStats(self,stats):
        output          = []

        # columnNames
        if not self.columnNames:
            self.columnNames = sorted(stats.keys())
            output     += ['\n# '+' '.join(self.columnNames)]

        # dataline
        formatString    = ' '.join(['{{{0}:>{1}}}'.format(i,len(k)) for (i,k) in enumerate(self.columnNames)])
        formatString   += '\n'

        vals = []
        for k in self.columnNames:
            if type(stats[k])==float:
                vals += ['{0:.3f}'.format(stats[k])]
            else:
                vals += [stats[k]]

        output += ['  '+formatString.format(*tuple(vals))]

        # write to file
        with open(self.settings.getOutputFile(),'a') as f:
            f.write('\n'.join(output))

    def _fileWriteTopology(self):
        output  = []
        output += [
            '#position of mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote id: {0} mote x,y coordinate: ({1:.5f},{2:.5f}) mote-rank: {3} \n'.format(mote.id,mote.x,mote.y,mote.getMoteRank()) for mote in self.engine.motes])
            )
        ]


        #printing the charge each mote has at run
        output += [
            '#charge cosumed by a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  chargeConsumed:@{1:.2f} \n'.format(mote.id,mote.getMoteStats()['chargeConsumed']) for mote in self.engine.motes])
            )
        ]
        #printing the txcells each mote has at this run
        output += [
            '#txcells of a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  txcells:{1} \n'.format(mote.id,mote.getMoteStats()['numTxCells']) for mote in self.engine.motes])
            )
        ]
        #printing the Rxcells each mote at this run
        output += [
            '#rxcells of a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  Rxcells:{1} \n'.format(mote.id,mote.getMoteStats()['numRxCells']) for mote in self.engine.motes])
            )
        ]
        #printing the average queue delay of each mote at this run
        output += [
            '#average queue delay by a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  average queue delay:{1} \n'.format(mote.id,mote.getMoteStats()['aveQueueDelay']) for mote in self.engine.motes])
            )
        ]
        #printing the average latency of each mote at this run
        output += [
            '#average latency by a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  average latency:{1} \n'.format(mote.id,mote.getMoteStats()['aveLatency']) for mote in self.engine.motes])
            )
        ]
        #printing the average hops of each mote at this run
        output += [
            '#average hops a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  average hops:{1} \n'.format(mote.id,mote.getMoteStats()['aveHops']) for mote in self.engine.motes])
            )
        ]
        #printing the numtx of each mote at this run
        output += [
            '#numTx of a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  numTx:{1} \n'.format(mote.id,mote.getMoteStats()['numTx']) for mote in self.engine.motes])
            )
        ]
        #printing the probableCollisions of each mote at this run
        output += [
            '#probable collisions a mote at runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  probableCollisions:{1} \n'.format(mote.id,mote.getMoteStats()['probableCollisions']) for mote in self.engine.motes])
            )
        ]
        #prinitng the average charge chargeConsumed by each mote at this run
        output += [
            '#aveChargePerCycle runNum={0} {1}\n'.format(
                self.runNum,
                ' '.join(['mote-id:{0}  averagechargeConsumed:@{1:.2f} \n'.format(mote.id,mote.getMoteStats()['chargeConsumed']/self.settings.numCyclesPerRun) for mote in self.engine.motes])
            )
        ]
        output  = '\n'.join(output)

        with open(self.settings.getOutputFile(),'a') as f:
            f.write(output)
