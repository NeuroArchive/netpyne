"""
cell.py

Contains Synapse, Conn, Cell and Population classes

Contributors: salvadordura@gmail.com
"""

from pylab import arange, seed, rand, array
from neuron import h # Import NEURON
import framework as f


###############################################################################
#
# GENERIC CELL CLASS
#
###############################################################################

class Cell(object):
    ''' Generic 'Cell' class used to instantiate individual neurons based on (Harrison & Sheperd, 2105) '''

    def __init__(self, gid, tags):
        self.gid = gid  # global cell id
        self.tags = tags  # dictionary of cell tags/attributes
        self.secs = {}  # dict of sections
        self.conns = []  # list of connections
        self.stims = []  # list of stimuli

        self.make()  # create cell
        self.associateGid() # register cell for this node

    def make(self):
        for prop in f.net.params['cellParams']:  # for each set of cell properties
            conditionsMet = 1
            for (condKey,condVal) in prop['conditions'].items():  # check if all conditions are met
                if self.tags[condKey] != condVal:
                    conditionsMet = 0
                    break
            if conditionsMet:  # if all conditions are met, set values for this cell
                if 'propList' not in self.tags:
                    self.tags['propList'] = [prop['label']] # create list of property sets
                else:
                    self.tags['propList'].append(prop['label'])  # add label of cell property set to list of property sets for this cell
                if f.cfg['createPyStruct']:
                    self.createPyStruct(prop)
                if f.cfg['createNEURONObj']:
                    self.createNEURONObj(prop)  # add sections, mechanisms, synapses, geometry and topolgy specified by this property set


    def createPyStruct(self, prop):
        # set params for all sections
        for sectName,sectParams in prop['sections'].items():
            # create section
            if sectName not in self.secs:
                self.secs[sectName] = {}  # create section dict
            sec = self.secs[sectName]  # pointer to section

            # add distributed mechanisms
            if 'mechs' in sectParams:
                for mechName,mechParams in sectParams['mechs'].items():
                    if 'mechs' not in sec:
                        sec['mechs'] = {}
                    if mechName not in sec['mechs']:
                        sec['mechs'][mechName] = {}
                    for mechParamName,mechParamValue in mechParams.items():  # add params of the mechanism
                        sec['mechs'][mechName][mechParamName] = mechParamValue

            # add point processes
            if 'pointps' in sectParams:
                for pointpName,pointpParams in sectParams['pointps'].items():
                    if self.tags['cellModel'] == pointpName:
                        if 'pointps' not in sec:
                            sec['pointps'] = {}
                        if pointpName not in sec['pointps']:
                            sec['pointps'][pointpName] = {}
                        for pointpParamName,pointpParamValue in pointpParams.items():  # add params of the mechanism
                            sec['pointps'][pointpName][pointpParamName] = pointpParamValue


            # add synapses
            if 'syns' in sectParams:
                for synName,synParams in sectParams['syns'].items():
                    if 'syns' not in sec:
                        sec['syns'] = {}
                    if synName not in sec['syns']:
                        sec['syns'][synName] = {}
                    for synParamName,synParamValue in synParams.items():  # add params of the synapse
                        sec['syns'][synName][synParamName] = synParamValue

            # add geometry params
            if 'geom' in sectParams:
                for geomParamName,geomParamValue in sectParams['geom'].items():
                    if 'geom' not in sec:
                        sec['geom'] = {}
                    if not type(geomParamValue) in [list, dict]:  # skip any list or dic params
                        sec['geom'][geomParamName] = geomParamValue

            # add 3d geometry
            if 'pt3d' in sectParams['geom']:
                if 'pt3d' not in sec['geom']:
                    sec['geom']['pt3d'] = []
                for pt3d in sectParams['geom']['pt3d']:
                    sec['geom']['pt3d'].append(pt3d)

            # add topolopgy params
            if 'topol' in sectParams:
                if 'topol' not in sec:
                    sec['topol'] = {}
                for topolParamName,topolParamValue in sectParams['topol'].items():
                    sec['topol'][topolParamName] = topolParamValue



    def createNEURONObj(self, prop):
        # set params for all sections
        for sectName,sectParams in prop['sections'].items():
            # create section
            if sectName not in self.secs:
                self.secs[sectName] = {}  # create sect dict if doesn't exist
            self.secs[sectName]['hSection'] = h.Section(name=sectName)  # create h Section object
            sec = self.secs[sectName]  # pointer to section

            # add distributed mechanisms
            if 'mechs' in sectParams:
                for mechName,mechParams in sectParams['mechs'].items():
                    if mechName not in sec['mechs']:
                        sec['mechs'][mechName] = {}
                    sec['hSection'].insert(mechName)
                    for mechParamName,mechParamValue in mechParams.items():  # add params of the mechanism
                        mechParamValueFinal = mechParamValue
                        for iseg,seg in enumerate(sec['hSection']):  # set mech params for each segment
                            if type(mechParamValue) in [list]:
                                mechParamValueFinal = mechParamValue[iseg]
                            seg.__getattribute__(mechName).__setattr__(mechParamName,mechParamValueFinal)

            # add point processes
            if 'pointps' in sectParams:
                for pointpName,pointpParams in sectParams['pointps'].items():
                    if self.tags['cellModel'] == pointpName:
                        if pointpName not in sec['pointps']:
                            sec['pointps'][pointpName] = {}
                        synObj = getattr(h, pointpName)
                        loc = pointpParams['loc'] if 'loc' in pointpParams else 0.5  # set location
                        sec['pointps'][pointpName]['hPointp'] = synObj(loc, sec = sec['hSection'])  # create h Syn object (eg. h.Ex)
                        for pointpParamName,pointpParamValue in pointpParams.items():  # add params of the synapse
                            if pointpParamName not in ['loc','vref','synList']:
                                setattr(sec['pointps'][pointpName]['hPointp'], pointpParamName, pointpParamValue)

            # add synapses
            if 'syns' in sectParams:
                for synName,synParams in sectParams['syns'].items():
                    if synName not in sec['syns']:
                        sec['syns'][synName] = {}
                    synObj = getattr(h, synParams['type'])
                    sec['syns'][synName]['hSyn'] = synObj(synParams['loc'], sec = sec['hSection'])  # create h Syn object (eg. h.Ex)
                    for synParamName,synParamValue in synParams.items():  # add params of the synapse
                        if synParamName not in ['type','loc']:
                            setattr(sec['syns'][synName]['hSyn'], synParamName, synParamValue)

            # set geometry params
            if 'geom' in sectParams:
                for geomParamName,geomParamValue in sectParams['geom'].items():
                    if not type(geomParamValue) in [list, dict]:  # skip any list or dic params
                        setattr(sec['hSection'], geomParamName, geomParamValue)

            # set 3d geometry
            if 'pt3d' in sectParams['geom']:
                h.pt3dclear(sec=sec['hSection'])
                x = self.tags['x']
                if 'yfrac' in self.tags and 'corticalthick' in f.net.params:
                    y = self.tags['yfrac'] * f.net.params['corticalthick']/1e3  # y as a func of yfrac and cortical thickness
                else:
                    y = self.tags['y']
                z = self.tags['z']
                for pt3d in sectParams['geom']['pt3d']:
                    h.pt3dadd(x+pt3d[0], y+pt3d[1], z+pt3d[2], pt3d[3], sec=sec['hSection'])

        # set topology
        for sectName,sectParams in prop['sections'].items():  # iterate sects again for topology (ensures all exist)
            sec = self.secs[sectName]  # pointer to section # pointer to child sec
            if 'topol' in sectParams:
                if sectParams['topol']:
                    sec['hSection'].connect(self.secs[sectParams['topol']['parentSec']]['hSection'], sectParams['topol']['parentX'], sectParams['topol']['childX'])  # make topol connection



    def associateGid (self, threshold = 10.0):
        if self.secs:
            f.pc.set_gid2node(self.gid, f.rank) # this is the key call that assigns cell gid to a particular node
            sec = self.secs['soma'] if 'soma' in self.secs else self.secs[list(self.secs.keys())[0]]  # use soma if exists, otherwise 1st section
            nc = None
            if 'pointps' in sec:  # if no syns, check if point processes (artificial cell)
                for pointpName, pointpParams in sec['pointps'].items():
                    if self.tags['cellModel'] == pointpName and 'vref' in pointpParams:
                        nc = h.NetCon(sec['pointps'][pointpName]['hPointp'].__getattribute__('_ref_'+pointpParams['vref']), None, sec=sec['hSection'])
                        break
            if not nc:  # if still haven't created netcon
                nc = h.NetCon(sec['hSection'](0.5)._ref_v, None, sec=sec['hSection'])
            nc.threshold = threshold
            f.pc.cell(self.gid, nc, 1)  # associate a particular output stream of events
            f.gidVec.append(self.gid) # index = local id; value = global id
            f.gidDic[self.gid] = len(f.gidVec)
            del nc # discard netcon



    def addConn(self, params):
        if params['preGid'] == self.gid:
            print ('Error: attempted to create self-connection on cell gid=%d, section=%s '%(self.gid, params['sec']))
            return  # if self-connection return

        if not params['sec']:  # if no section specified
            if 'soma' in self.secs:
                params['sec'] = 'soma'  # use 'soma' if exists
            elif self.secs:
                params['sec'] = list(self.secs.keys())[0]  # if no 'soma', use first sectiona available
            else:
                print ('Error: no Section available on cell gid=%d to add connection'%(self.gid))
                return  # if no Sections available print error and exit

        weightIndex = 0  # set default weight matrix index

        pointp = None
        if 'pointps' in self.secs[params['sec']]:  #  check if point processes (artificial cell)
            for pointpName, pointpParams in self.secs[params['sec']]['pointps'].items():
                if self.tags['cellModel'] == pointpName and 'vref' in pointpParams:  # if includes vref param means doesn't use Section v or synapses
                    pointp = pointpName
                    if 'synList' in pointpParams:
                        if params['synReceptor'] in pointpParams['synList']:
                            weightIndex = pointpParams['synList'].index(params['synReceptor'])  # udpate weight index based pointp synList

        if not params['synReceptor']:  # if no synapse specified
            if 'syns' in self.secs[params['sec']]:
                params['synReceptor'] = list(self.secs[params['sec']]['syns'].keys())[0]  # use first synapse available in section

        if not params['synReceptor']:  # if still no synapse
                print ('Error: no Synapse or point process available on cell gid=%d, section=%s to add connection'%(self.gid, params['sec']))
                return  # if no Synapse available print error and exit

        if not params['threshold']:
            params['threshold'] = 10.0

        self.conns.append(params)
        if pointp:
            netcon = f.pc.gid_connect(params['preGid'], self.secs[params['sec']]['pointps'][pointp]['hPointp']) # create Netcon between global gid and local point neuron
        else:
            netcon = f.pc.gid_connect(params['preGid'], self.secs[params['sec']]['syns'][params['synReceptor']]['hSyn']) # create Netcon between global gid and local synapse

        netcon.weight[weightIndex] = params['weight']  # set Netcon weight
        netcon.delay = params['delay']  # set Netcon delay
        netcon.threshold = params['threshold']  # set Netcon delay
        self.conns[-1]['hNetcon'] = netcon  # add netcon object to dict in conns list
        if f.cfg['verbose']: print('Created connection preGid=%d, postGid=%d, sec=%s, syn=%s, weight=%.2f, delay=%.1f'%
            (params['preGid'], self.gid, params['sec'], params['synReceptor'], params['weight'], params['delay']))


    def addStim (self, params):
        if not params['sec']:  # if no section specified
            if 'soma' in self.secs:
                params['sec'] = 'soma'  # use 'soma' if exists
            elif self.secs:
                params['sec'] = list(self.secs.keys())[0]  # if no 'soma', use first sectiona available
            else:
                print ('Error: no Section available on cell gid=%d to add connection'%(self.gid))
                return  # if no Sections available print error and exit

        weightIndex = 0  # set default weight matrix index

        pointp = None
        if 'pointps' in self.secs[params['sec']]:  # if no syns, check if point processes (artificial cell)
            for pointpName, pointpParams in self.secs[params['sec']]['pointps'].items():
                  if self.tags['cellModel'] == pointpName and 'vref' in pointpParams:  # if includes vref param means doesn't use Section v or synapses
                    pointp = pointpName
                    if 'synList' in pointpParams:
                        if params['synReceptor'] in pointpParams['synList']:
                            weightIndex = pointpParams['synList'].index(params['synReceptor'])  # udpate weight index based pointp synList


        if not params['synReceptor']:  # if no synapse specified
            if 'syns' in self.secs[params['sec']]:
                params['synReceptor'] = list(self.secs[params['sec']]['syns'].keys())[0]  # use first synapse available in section

        if not params['synReceptor']:  # if still no synapse
                print ('Error: no Synapse or point process available on cell gid=%d, section=%s to add stim'%(self.gid, params['sec']))
                return  # if no Synapse available print error and exit

        if not params['threshold']:
            params['threshold'] = 10.0

        self.stims.append(params)

        if params['source'] == 'random':
            rand = h.Random()
            rand.Random123(self.gid,self.gid*2)
            rand.negexp(1)
            self.stims[-1]['hRandom'] = rand  # add netcon object to dict in conns list

            netstim = h.NetStim()
            netstim.interval = params['rate']**-1*1e3 # inverse of the frequency and then convert from Hz^-1 to ms
            netstim.noiseFromRandom(rand)  # use random number generator
            netstim.noise = params['noise']
            netstim.number = 1e12
            self.stims[-1]['hNetStim'] = netstim  # add netstim object to dict in stim list

        if pointp:
            netcon = h.NetCon(netstim, self.secs[params['sec']]['pointps'][pointp]['hPointp'])  # create Netcon between global gid and local point neuron
        else:
            netcon = h.NetCon(netstim, self.secs[params['sec']]['syns'][params['synReceptor']]['hSyn']) # create Netcon between global gid and local synapse
        netcon.weight[weightIndex] = params['weight']  # set Netcon weight
        netcon.delay = params['delay']  # set Netcon delay
        netcon.threshold = params['threshold']  # set Netcon delay
        self.stims[-1]['hNetcon'] = netcon  # add netcon object to dict in conns list
        if f.cfg['verbose']: print('Created stim prePop=%s, postGid=%d, sec=%s, syn=%s, weight=%.2f, delay=%.1f'%
            (params['popLabel'], self.gid, params['sec'], params['synReceptor'], params['weight'], params['delay']))

    def recordTraces (self):
        # set up voltagse recording; recdict will be taken from global context
        for key, params in f.cfg['recdict'].items():
            ptr = None
            try:
                if 'pos' in params:
                    if 'mech' in params:  # eg. soma(0.5).hh._ref_gna
                        ptr = self.secs[params['sec']]['hSection'](params['pos']).__getattribute__(params['mech']).__getattribute__('_ref_'+params['var'])
                    elif 'syn' in params:  # eg. soma(0.5).AMPA._ref_g
                        ptr = self.secs[params['sec']]['syns'][params['syn']]['hSyn'].__getattribute__('_ref_'+params['var'])
                    else:  # eg. soma(0.5)._ref_v
                        ptr = self.secs[params['sec']]['hSection'](params['pos']).__getattribute__('_ref_'+params['var'])
                else:
                    if 'pointp' in params: # eg. soma.izh._ref_u
                        #print self.secs[params['sec']]
                        if params['pointp'] in self.secs[params['sec']]['pointps']:
                            ptr = self.secs[params['sec']]['pointps'][params['pointp']]['hPointp'].__getattribute__('_ref_'+params['var'])

                if ptr:  # if pointer has been created, then setup recording
                    f.simData[key]['cell_'+str(self.gid)] = h.Vector(f.cfg['tstop']/f.cfg['recordStep']+1).resize(0)
                    f.simData[key]['cell_'+str(self.gid)].record(ptr, f.cfg['recordStep'])
                    if f.cfg['verbose']: print ('Recording ', key, 'from cell ', self.gid)
            except:
                if f.cfg['verbose']: print ('Cannot record ', key, 'from cell ', self.gid)


    def recordStimSpikes (self):
        f.simData['stims'].update({'cell_'+str(self.gid): {}})
        for stim in self.stims:
            stimSpikeVecs = h.Vector() # initialize vector to store
            stim['hNetcon'].record(stimSpikeVecs)
            f.simData['stims']['cell_'+str(self.gid)].update({stim['popLabel']: stimSpikeVecs})


    def __getstate__(self):
        ''' Removes non-picklable h objects so can be pickled and sent via py_alltoall'''
        odict = self.__dict__.copy() # copy the dict since we change it
        odict = f.sim.replaceItemObj(odict, keystart='h', newval=None)  # replace h objects with None so can be pickled
        return odict



###############################################################################
#
# POINT NEURON CLASS (v not from Section)
#
###############################################################################

class PointNeuron(Cell):
    '''
    Point Neuron that doesn't use v from Section - TO DO
    '''
    pass


###############################################################################
#
# POP CLASS
#
###############################################################################

class Pop(object):
    ''' Python class used to instantiate the network population '''
    def __init__(self,  tags):
        self.tags = tags # list of tags/attributes of population (eg. numCells, cellModel,...)
        self.cellGids = []  # list of cell gids beloging to this pop

    # Function to instantiate Cell objects based on the characteristics of this population
    def createCells(self):

        # add individual cells
        if 'cellsList' in self.tags:
            cells = self.createCellsList()

        # if NetStim pop do not create cell objects (Netstims added to postsyn cell object when creating connections)
        elif self.tags['cellModel'] == 'NetStim':
            cells = []

        # create cells based on fixed number of cells
        elif 'numCells' in self.tags:
            cells = self.createCellsFixedNum()

        # create cells based on density (optional yfrac-dep)
        elif 'yfracRange' in self.tags and 'density' in self.tags:
            cells = self.createCellsDensity()

        # not enough tags to create cells
        else:
            cells = []
            if 'popLabel' not in self.tags:
                self.tags['popLabel'] = 'unlabeled'
            print( 'Not enough tags to create cells of population %s'%(self.tags['popLabel']))

        return cells


    # population based on numCells
    def createCellsFixedNum(self):
        cellModelClass = Cell
        cells = []
        for i in range(int(f.rank), self.tags['numCells'], f.nhosts):
            gid = f.lastGid+i
            self.cellGids.append(gid)  # add gid list of cells belonging to this population - not needed?
            cellTags = {k: v for (k, v) in self.tags.items() if k in f.net.params['popTagsCopiedToCells']}  # copy all pop tags to cell tags, except those that are pop-specific
            cellTags['y'] = 0 # set yfrac value for this cell
            cellTags['x'] = 0  # calculate x location (um)
            cellTags['z'] = 0 # calculate z location (um)
            if 'propList' not in cellTags: cellTags['propList'] = []  # initalize list of property sets if doesn't exist
            cells.append(cellModelClass(gid, cellTags)) # instantiate Cell object
            if f.cfg['verbose']: print('Cell %d/%d (gid=%d) of pop %s, on node %d, '%(i, self.tags['numCells']-1, gid, self.tags['popLabel'], f.rank))
        f.lastGid = f.lastGid + self.tags['numCells']
        return cells


    # population based on YfracRange
    def createCellsDensity(self):
        cellModelClass = Cell
        cells = []
        volume = f.net.params['scale'] * f.net.params['sparseness'] * (f.net.params['modelsize']/1e3)**2 \
             * ((self.tags['yfracRange'][1]-self.tags['yfracRange'][0]) * f.net.params['corticalthick']/1e3)  # calculate num of cells based on scale, density, modelsize and yfracRange

        if hasattr(self.tags['density'], '__call__'): # check if conn is yfrac-dep density func
            yfracInterval = 0.001  # interval of yfrac values to evaluate in order to find the max cell density
            maxDensity = max(map(self.tags['density'], (arange(self.tags['yfracRange'][0],self.tags['yfracRange'][1], yfracInterval))))  # max cell density
            maxCells = volume * maxDensity  # max number of cells based on max value of density func

            seed(f.sim.id32('%d' % f.cfg['randseed']))  # reset random number generator
            yfracsAll = self.tags['yfracRange'][0] + ((self.tags['yfracRange'][1]-self.tags['yfracRange'][0])) * rand(int(maxCells), 1)  # random yfrac values
            yfracsProb = array(map(self.tags['density'], yfracsAll)) / maxDensity  # calculate normalized density for each yfrac value (used to prune)
            allrands = rand(len(yfracsProb))  # create an array of random numbers for checking each yfrac pos

            makethiscell = yfracsProb>allrands  # perform test to see whether or not this cell should be included (pruning based on density func)
            yfracs = [yfracsAll[i] for i in range(len(yfracsAll)) if i in array(makethiscell.nonzero()[0],dtype='int')] # keep only subset of yfracs based on density func
            self.tags['numCells'] = len(yfracs)  # final number of cells after pruning of yfrac values based on density func
            if f.cfg['verbose']: print ('Volume=%.2f, maxDensity=%.2f, maxCells=%.0f, numCells=%.0f'%(volume, maxDensity, maxCells, self.tags['numCells']))

        else:  # NO yfrac-dep
            self.tags['numCells'] = int(self.tags['density'] * volume)  # = density (cells/mm^3) * volume (mm^3)
            seed(f.sim.id32('%d' % f.cfg['randseed']))  # reset random number generator
            yfracs = self.tags['yfracRange'][0] + ((self.tags['yfracRange'][1]-self.tags['yfracRange'][0])) * rand(self.tags['numCells'], 1)  # random yfrac values
            if f.cfg['verbose']: print ('Volume=%.4f, density=%.2f, numCells=%.0f'%(volume, self.tags['density'], self.tags['numCells']))

        randLocs = rand(self.tags['numCells'], 2)  # create random x,z locations

        for i in xrange(int(f.rank), self.tags['numCells'], f.nhosts):
            gid = f.lastGid+i
            self.cellGids.append(gid)  # add gid list of cells belonging to this population - not needed?
            cellTags = {k: v for (k, v) in self.tags.items() if k in f.net.params['popTagsCopiedToCells']}  # copy all pop tags to cell tags, except those that are pop-specific
            cellTags['yfrac'] = yfracs[i][0]  # set yfrac value for this cell
            cellTags['x'] = f.net.params['modelsize'] * randLocs[i,0]  # calculate x location (um)
            cellTags['z'] = f.net.params['modelsize'] * randLocs[i,1]  # calculate z location (um)
            if 'propList' not in cellTags: cellTags['propList'] = []  # initalize list of property sets if doesn't exist
            cells.append(cellModelClass(gid, cellTags)) # instantiate Cell object
            if f.cfg['verbose']:
                print('Cell %d/%d (gid=%d) of pop %s, pos=(%2.f, %2.f, %2.f), on node %d, '%(i, self.tags['numCells']-1, gid, self.tags['popLabel'],cellTags['x'], cellTags['yfrac'], cellTags['z'], f.rank))
        f.lastGid = f.lastGid + self.tags['numCells']
        return cells


    def createCellsList(self):
        cellModelClass = Cell
        cells = []
        self.tags['numCells'] = len(self.tags['cellsList'])
        for i in xrange(int(f.rank), len(self.tags['cellsList']), f.nhosts):
            if 'cellModel' in self.tags['cellsList'][i]:
                cellModelClass = getattr(f, self.tags['cellsList'][i]['cellModel'])  # select cell class to instantiate cells based on the cellModel tags
            gid = f.lastGid+i
            self.cellGids.append(gid)  # add gid list of cells belonging to this population - not needed?
            cellTags = {k: v for (k, v) in self.tags.items() if k in f.net.params['popTagsCopiedToCells']}  # copy all pop tags to cell tags, except those that are pop-specific
            cellTags.update(self.tags['cellsList'][i])  # add tags specific to this cells
            if 'propList' not in cellTags: cellTags['propList'] = []  # initalize list of property sets if doesn't exist
            cells.append(cellModelClass(gid, cellTags)) # instantiate Cell object
            if f.cfg['verbose']: print('Cell %d/%d (gid=%d) of pop %d, on node %d, '%(i, self.tags['numCells']-1, gid, i, f.rank))
        f.lastGid = f.lastGid + len(self.tags['cellsList'])
        return cells


    def __getstate__(self):
        ''' Removes non-picklable h objects so can be pickled and sent via py_alltoall'''
        odict = self.__dict__.copy() # copy the dict since we change it
        odict = f.sim.replaceFuncObj(odict)  # replace h objects with None so can be pickled
        return odict
