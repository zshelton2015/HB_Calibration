#!/usr/bin/env python
from datetime import date, datetime
from time import sleep
import os
from optparse import OptionParser
import subprocess
import sys
import numpy
#from numpy import std, mean
from ROOT import *
import re
from array import array
import pickle
from ast import literal_eval


from getPedestals import *

from fitGraphs_linearized_2d import *
from adcTofC_linearized_2d import cleanGraph,makeADCvsfCgraphSepCapID
from GraphParamDist_2d import *

from FitUncertaintyPlots import fillFitUncertaintyHists 

slotDict = {1:[18,19,20,21,23,24,25,26],
            }

shunt_GSel ={1:0,
            1.5:1,
            2:2,
            3:4,
            4:8,
            5:16,
            6:18,
            7:20,
            8:24,
            9:26,
            10:28,
            11:30,
            11.5:31}        
shuntMultList = shunt_GSel.keys()
shuntMultList.sort()
#Barcode_UID ={hex(0xead4b070):600028,
#         hex(0xeabb9870):600549,
#         hex(0xeab47170):600639,
#         hex(0xead65570):600709,
#         hex(0xeacc8d70):600458,
#         hex(0xea93f270):600425,
#         hex(0xeacd8870):600426,
#         hex(0xea9db770):600429,
#         hex(0xeabb1f70):600489,
#         hex(0xeaaeaa70):600033,
#         hex(0xeabfc070):600078,
#         hex(0xeaa7ef70):600095,
#         hex(0xeabcff70):600106,
#         hex(0xead3d470):600463,
#         hex(0xea9e6d70):600501,
#         hex(0xeaa72770):600670}
         # hex(0xead5c870):600064,
         # hex(0xead60170):600658}  
#BarcodeList = Barcode_UID.keys()
#BarcodeList.sort()
#print BarcodeList
#sys.exit()

import sqlite3 as lite

#barcode_UID = sqlite3.connect("/Users/titasroy/Downloads/serialNumberToUIDmap.db")

#cursor = barcode_UID.cursor()


mg = TMultiGraph()

from read_histo_2d import read_histo_2d



gROOT.SetBatch(kTRUE)

orbitDelay = 30
GTXreset = 1
CDRreset = 0

### Which slot number contains which injection card {slot:card}
### slots are numbered 1 to 8 (slot 10 contains the DAC, slot 9 has an extra injection card)
### The purpose of this dictionary is to allow for swapping out a nonfunctional card
injectionCardSlotMapping = {1:1,
                            2:2,
                            3:3,
                            4:4,
                            5:5,
                            6:6,
                            7:7,
                            8:8,
                            }

fakesimpleCardMap = {1  : 1 , 2  : 2 , 3  : 3 , 4  : 4 , 5  : 5 , 6  : 6 , 7  : 7 , 8  : 8 , 9  : 9 , 10 : 10, 11 : 11, 12 : 12, 13 : 13, 14 : 14, 15 : 15, 16 : 16, 17 : 17, 18 : 18, 19 : 19, 20 : 20, 21 : 21, 22 : 22, 23 : 23, 24 : 24, 25 : 25, 26 : 26, 27 : 27, 28 : 28, 29 : 29, 30 : 30, 31 : 31, 32 : 32,
                             }

def getValuesFromFile(outputDir):
    """
    Gets data from the cardData text file from the previous run
    Gets things like the injection mapping, QIE ranges used, etc.
    """
    
    return {}, {}

    dataFile = open(outputDir+"/cardData.txt",'r')
    for line in dataFile:
        if 'DAC' in line and 'Used' in line:
            dacNumber = line.split()[1]
        if 'linkMap' in line:
            linkMap = eval(line.split('linkMap')[-1])
        if 'injectionCardMap' in line:
            injectionCardMap = eval(line.split('injectionCardMap')[-1])
    return linkMap, injectionCardMap 
            

def ShuntScan(shuntMult=1, outputDirectory = '', linkMap={},injectionCardMap={}, histoMap={}, histoList = '-1'):
    files = os.listdir(outputDirectory)
    final_file = ''
    for f in files:
        if 'QIECalibration_' in f:
            final_file = outputDirectory+f
    if final_file=='':
        print 'Unable to find data file in directory %s'%outputDirectory
        print 'Exiting'
        sys.exit()

    #linkMap, injectionCardMap = getValuesFromFile(outputDirectory)

    #linkMap, injectionCardMap = getValuesFromFile(outputDirectory)
    val, meanvals, rmsvals, charge= read_histo_2d(file_in=final_file,shuntMult=shuntMult,linkMap=linkMap, injectionCardMap=injectionCardMap, histoMap=histoMap, histoList=histoList)
     
    return val, meanvals, rmsvals, charge


def QIECalibrationFit(_Directory, _histoList='-1', _shuntList='-1', _saveGraphs=False, logOutput = False):



    if _Directory[-1] != "/":
        _Directory += "/"
    #outputDirectory = _Directory + '/'
    outputDirectory = _Directory
    # rootfile = _filename
    # final_file = outputDirectory+rootfile
    
    # print "the root file is %s"%rootfile
    print "Reading from directory %s"%outputDirectory
    # print "final file is %s"%final_file

    if logOutput:
        originalSTDOUT = sys.stdout
        
        stdOutDump = open("%s/calibrationFitOutput.stdout"%outputDirectory, 'w')
        sys.stdout = stdOutDump

    # print "the root file is %s"%rootfile
    print "Reading from directory %s"%outputDirectory
    # print "final file is %s"%final_file


    # TODO: Fix this
    #linkMap, injectionCardMap = getValuesFromFile(outputDirectory)
    linkMap = {0,1}
    injectionCardMap = {}
    simpleCardMap = fakesimpleCardMap


    # Get histoMap
    with open(outputDirectory + "histoMap.txt", "r") as f:
        for i,line in enumerate(f):
            if line[0] == "#":
                # Skip comments
                continue
            histoMap = dict(literal_eval(line))


    # if _histoList == '-1':
    #     histoList = range(196)
    # else:
    #     histoList = eval(_histoList)

    # if type(histoList)==type(int()):
    #     histoList = [histoList]
    # histoList.sort()

    linkMaphistoList = []
    #print linkMap
    for link in linkMap:
        linkMaphistoList += [link*8,link*8+1,link*8+2,link*8+3,link*8+4,link*8+5,link*8+6,link*8+7]

    linkMaphistoList.sort()

    #histoList = list(set(histoList).intersection(linkMaphistoList))

    #histoList.sort()



    histoList = sorted(histoMap.keys())
    if not _histoList == '-1':
        histoList = eval(_histoList)
        if type(histoList)==type(int()):
            histoList = [histoList]
        histoList.sort()

    print '-'*30
    print 'Histograms List'
    print '-'*30
    print histoList


    outputParamFile = open(outputDirectory+"calibrationParams.txt",'w')
    outputParamFile.write('(qieID, barcode, qieNum, capID, qieRange,shuntMult,Gsel,slope,offset,uncertainty,maxResidual, QIboard, QIchannel)\n')

    uID_list = []

    #barcode_UID = sqlite3.connect("/Users/titasroy/Downloads/serialNumberToUIDmap.db")

    #cursor = barcode_UID.cursor()
    #Barcode_List ={}
    #for link in linkMap:
        #uID = linkMap[link]['unique_ID'] #.replace(' ','_')
        #cursor.execute('SELECT serial FROM UIDtoSerialNumber WHERE UID="%s"'%(uID))
        #Barcode_List.update({'%s'%(uID):'%i'%(cursor.fetchone()[0])})           
        #if uID not in uID_list:    
        #   uID_list.append(linkMap[link]['unique_ID'].replace(' ','_'))

    #uID_list =list(set(uID_list))   
#   print  Barcode_List
    # TODO: Fix this
    for _h in histoMap.values():
        uid = _h["UniqueID"]
        if uid not in uID_list:
            uID_list.append(uid)
    
    #uID_list = ["0x21000000_0xEAB30870"]
    
    
    print uID_list
#   sys.exit()
    qieParams={}
    cursor = {}
    for uID in uID_list:
        outputGraphFile = TFile("%s/fitResults_%s.root"%(outputDirectory, uID),"recreate")
#        outputGraphFile.mkdir("adcVsCharge")
        outputGraphFile.mkdir("LinadcVsCharge")
        outputGraphFile.mkdir("fitLines")
#        outputGraphFile.mkdir("Shunted_adcVsCharge")
        outputGraphFile.mkdir("Shunted_LinadcVsCharge")
        outputGraphFile.mkdir("Shunted_fitLines")
        outputGraphFile.mkdir("SummaryPlots")
        outputGraphFile.Close()

        qieParams[uID] = lite.connect(outputDirectory+"qieCalibrationParameters_%s.db"%(uID))
        cursor[uID] = qieParams[uID].cursor()
        cursor[uID].execute("drop table if exists qieshuntparams")
        #cursor[uID].execute("drop table if exists qieparams")
        #cursor[uID].execute("drop table if exists qietdcparams")

        cursor[uID].execute("create table if not exists qieshuntparams(id STRING, barcode STRING, qie INT, capID INT, range INT, shunt INT, Gsel INT, slope REAL, offset REAL, uncertainty REAL, maxResidual REAL, QIboard INT, QIchannel INT, fiber INT, fiberCH INT, runDirectory STRING)")




    ### Graph parameters
    outputParamFile_shunt = open(outputDirectory+"calibrationParams_shunt.txt",'w')
    outputParamFile_shunt.write('(qieID, barcode, qieNum, capID, qieRange, shuntMult, Gsel,slope, offset, uncertainty, maxResidual, QIboard, QIchannel)\n') 
    
    if _shuntList == '-1':
        shuntMult_list = shunt_GSel.keys()
    else:
        shuntMult_list = eval(_shuntList)

    if type(shuntMult_list)==type(int()):
        shuntMult_list = [shuntMult_list]
    shuntMult_list.sort()


    pedestalVals = {}


    pedestal_graphs_shunt ={}
    
    #shuntMult_list = [1.0]
    print "shuntMult_list = ", shuntMult_list
    for shuntMult in shuntMult_list:
        output={}
        shuntOutputDirectory = outputDirectory #+ "Data_%s_%s/"%(rangeMode, shuntMode)
        vals, meanvals, rmsvals, charge = ShuntScan(shuntMult=shuntMult, outputDirectory=outputDirectory, linkMap=linkMap,injectionCardMap=injectionCardMap, histoMap=histoMap, histoList=histoList)
        
        
        pedestal_graphs_shunt[shuntMult] = makeADCvsfCgraphSepCapID(vals[0],meanvals, rmsvals, charge, histoList,linkMap=linkMap,injectionCardMap=injectionCardMap,qieRange=0,shuntMult=shuntMult)

     
    dirStructure = outputDirectory.split('/')
    for value in dirStructure:
        if '2018' in value:
            date = value
        elif 'Run' in value:
            run = value
        else:
            run = 0
    #print dirStructure
    #print date
    #print run
    _filePeds = TFile("%sPedestalPlots/pedestalMeasurement_%s_%s.root"%(outputDirectory,date, run),"recreate")
    _filePeds.Close()
    print "Now Get Pedestals"
    pickle.dump(pedestal_graphs_shunt, open("debug.p", "wb"))
    pedestalVals = getPedestals(pedestal_graphs_shunt,shuntMult_list,histoList,outputDirectory, date, run)

    #print "-"*20
    #print "-"*20
    #print "PedestalValues"
    #print pedestalVals
    #print "-"*20
    #print "-"*20

    unshunted_params={}
    shuntFactors={}


    for shuntMult in shuntMult_list:
        shuntFactors[shuntMult]={}
        graphs_shunt ={}
        output={}
        print "Now on shuntMult %.1f"%shuntMult
        shuntOutputDirectory = outputDirectory #+ "Data_%s_%s/"%(rangeMode, shuntMode)
        vals, meanvals, rmsvals, charge = ShuntScan(shuntMult=shuntMult, outputDirectory=outputDirectory,histoMap=histoMap, histoList=histoList)
        print "this is:",outputDirectory
        if shuntMult == 1:
            qieRange= range(4)
        else:
            qieRange=range(2) 

        for i_range in qieRange:
#           histoList =  vals[i_range].keys()
#           histoList.sort()
        
            graphs_shunt[i_range] = makeADCvsfCgraphSepCapID(vals[i_range],meanvals, rmsvals, charge, histoList,linkMap=linkMap,injectionCardMap=injectionCardMap,qieRange=i_range,shuntMult=shuntMult)

#       print  Barcode_List
        #for ih in histoList:
        for ih in histoList:
            # TODO: Fix this 
            #linkNum = int(ih/8)
            linkNum = histoMap[ih]["Link"]
            #qieID = linkMap[linkNum]['unique_ID']
            qieID = histoMap[ih]["UniqueID"]
            barcode = histoMap[ih]["Barcode"]
            #barcode = 123456
            #print qieID
            
            #barcode = Barcode_List[qieID] 
                

            #print "Barcode is:",barcode
            #qieNum =ih%16 + 1
            qieNum = histoMap[ih]["QIE"]
            graphList_shunt=[]

            if 0 in graphs_shunt:
                graphList_shunt.append(graphs_shunt[0][ih])
            else:
                graphList_shunt.append(None)
            if 1 in graphs_shunt:
                graphList_shunt.append(graphs_shunt[1][ih])
            else:   
                graphList_shunt.append(None)
            if 2 in graphs_shunt:
                graphList_shunt.append(graphs_shunt[2][ih])
            else:
                graphList_shunt.append(None)
            if 3 in graphs_shunt:
                graphList_shunt.append(graphs_shunt[3][ih])
            else:
                graphList_shunt.append(None)
            if shuntMult ==1 :
                params_shunt, high_ranges =  doFit_combined(graphList = graphList_shunt, saveGraph = _saveGraphs, qieNumber = qieNum, qieBarcode = barcode, qieUniqueID = qieID, useCalibrationMode = False, outputDir = outputDirectory, shuntMult=shuntMult, pedestalVals = pedestalVals[ih])
                unshunted_params[ih]=high_ranges
            else:
                params_shunt, high_vals =  doFit_combined(graphList = graphList_shunt, saveGraph = _saveGraphs, qieNumber = qieNum, qieBarcode = barcode, qieUniqueID = qieID, useCalibrationMode = False, outputDir = outputDirectory, shuntMult=shuntMult, pedestalVals = pedestalVals[ih])


            #unshunted_params[ih]=high_ranges

            uID = qieID.replace(' ', '_')


            method1shunts = []
            for i_range in range(2): #change
                for i_capID in range(4):
                    if not params_shunt[i_range][i_capID][0]==0:
                        method1shunts.append(unshunted_params[ih][i_range][i_capID][0]/params_shunt[i_range][i_capID][0])
                    else: method1shunts.append(-1.)

            method1ShuntFactor = numpy.mean(method1shunts)
            method1ShuntFactorRMS = numpy.std(method1shunts)

                
            for i_range in range(4):
                for i_capID in range(4):
                    if shuntMult==1 or (i_range in [0,1]):
                        #print shuntMult, i_range
                        values_shunt = (qieID, barcode, qieNum, i_capID, i_range, shuntMult,shunt_GSel[shuntMult], (params_shunt[i_range][i_capID][0]),(params_shunt[i_range][i_capID][1]),(params_shunt[i_range][i_capID][2]), (params_shunt[i_range][i_capID][3]), histoMap[ih]["QIboard"], histoMap[ih]["QIchannel"], histoMap[ih]["Link"], ih%8, outputDirectory)
                        cursor[uID].execute("insert into qieshuntparams values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",values_shunt)
                    
                    #elif ( (shuntMult in [1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11.5]) and (i_range in [2,3]) ): #change
                    #    values_shunt = (qieID, barcode, qieNum, i_capID, i_range, shuntMult, shunt_GSel[shuntMult], (unshunted_params[ih][i_range][i_capID][0]/method1ShuntFactor),(unshunted_params[ih][i_range][i_capID][1]/method1ShuntFactor),(method1ShuntFactorRMS))
                     #   cursor[uID].execute("insert into qieshuntparams values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)",values_shunt)

                    outputParamFile_shunt.write(str(values_shunt)+'\n')
             
    outputParamFile_shunt.close()

    for uID in uID_list:
        print uID
        cursor[uID].close()
        qieParams[uID].commit()
        qieParams[uID].close()

    
    problemCards = []
    for uID in uID_list:
        #graphParamDist(outputDirectory+"qieCalibrationParameters_%s.db"%uID)
        
        outputFileName = "%s/fitResults_%s.root"%(outputDirectory, uID)
        badChannels = fillFitUncertaintyHists(outputFileName)
        if len(badChannels) > 0:
            slot = -1
            for h in histoList:#histoMap.keys():
                if histoMap[h]['UniqueID'] == uID:
                    (_rm,_slot) = (histoMap[h]["RM"], histoMap[h]["Slot"])
            problemCards.append([_rm, _slot, uID])
    
    
    with open("problemCards.txt", "w") as f:
        f.write("Probem cards from %s Run %d\n" % (date, run))
        f.write("RM\tSlot\tUniqueID\n")
        for card in problemCards:
            print '*'*40
            print 'PROBLEM WITH FIT IN QIE CARD'
            print '    RM %d Slot %d  UniqueID %s'% (card[0], card[1], card[2])
            f.write("%d\t%d\t%s\n" % (card[0], card[1], card[2]))

    if logOutput:
        sys.stdout = originalSTDOUT


                
if __name__ == "__main__":
    parser = OptionParser()
    # parser.add_option("-r", "--range", dest="range", default=-1,type='int',
    #                   help="Specify range to be used in scan (default is -1, which does all 4 ranges)" )
    # parser.add_option("--NoSepCapID", action="store_false",dest="sepCapID",default=True,
    #                   help="don't separate the different capID histograms")
    # parser.add_option("--SkipScan", action="store_true",dest="SkipScan",default=False,
    #                   help="Skip the scan, using presaved scan")
    # parser.add_option("--SkipFit", action="store_true",dest="SkipFit",default=False,
    #                   help="Skip the fitting step")
    # parser.add_option("--NoLinkInit", action="store_true",dest="NoLinkInit",default=False,
    #                   help="Skip the scan, using presaved scan")
    # parser.add_option("--SkipTDC", action="store_false",dest="RunTDCScan",default=True,
    #                   help="Skip the TDC scans")
    # parser.add_option("--SkipShunt", action="store_false",dest="RunShunt",default=True,
    #                   help="Skip the Shunt Scans")
    parser.add_option("--shuntList", dest="shuntList",default="-1",type="str",
                      help="List of shunts to run on, default is -1, which will run all the shunts")
    parser.add_option("-d","--dir", dest="Directory",default="",type="str",
                      help="Data file from previous data taking run to redo the fit on")
    # parser.add_option("-f","--filename",dest="filename",default="",type="str",
    #                   help="Data file from previous data taking run to redo the fit on")
    parser.add_option("--saveGraph","--savegraph","--saveGraphs","--savegraphs",action="store_true",dest="saveGraphs",default=False,
                     help="Save Graphs")
    parser.add_option("--histoList", dest="histoList",default="-1",type="str",
                      help="List of histos to run on, default is -1, which will run all the histograms")
    (options, args) = parser.parse_args()
    print 'start'

#    QIECalibrationScan(options)
    QIECalibrationFit(_Directory=options.Directory, _histoList = options.histoList, _shuntList = options.shuntList, _saveGraphs = options.saveGraphs)
