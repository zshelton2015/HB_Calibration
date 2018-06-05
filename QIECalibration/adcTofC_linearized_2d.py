from ROOT import *
import sys
import re
from array import array 
import os
import string
import sqlite3 as lite
import csv
from linearADC import *
from read_histo_2d import *


#c1 = TCanvas('c1', 'Plots', 1000, 500)
#c1.SetFillColor(0)
#c1.SetGrid()
gROOT.SetBatch(kTRUE)
nominalMapping = { 1 : 4,
                   2 : 4,
                   3 : 4,
                   4 : 4,
                   5 : 1,
                   6 : 2,
                   7 : 4,
                   8 : 4,
                   }


def cleanGraph(graph,i_range):

    N = graph.GetN()
    topPoints = range(int(N/2),N)
    botPoints = range(int(N/2))
    botPoints.reverse()

#     points = range(graph.GetN())
#     points.reverse()

    MinSaveValue = linADC(i_range*64 + 2)[0]
    MaxSaveValue = linADC(i_range*64 + 61)[0]

    maxPointNumber = 999
    minPointNumber = -1


    #Identify the last point to keep
    for p in topPoints:
        if graph.GetY()[p] > MaxSaveValue:
            maxPointNumber = p
            break

    #Identify the first point to keep
    for p in botPoints:
        if graph.GetY()[p] < MinSaveValue:
            minPointNumber = p+1
            break

#     #Identify the first and last points to keep                                                                               
#     for p in points:

#         if graph.GetY()[p] > MaxSaveValue:
#             maxPointNumber = p

#         if graph.GetY()[p] > MinSaveValue:
#             minPointNumber = p

        
    #remove everything after the last point                                                                                   
    if maxPointNumber <999:
        while (graph.GetN() > maxPointNumber):
            graph.RemovePoint(maxPointNumber)

    #remove the first N points, where N = minPointNumber                                                                      
    if minPointNumber >-1:
        for i in range(minPointNumber):
            graph.RemovePoint(0)

    while graph.GetY()[0] > graph.GetY()[1]:
        graph.RemovePoint(0)
    
    if graph.GetN()==0:
        print "Found a graph with no points!!!!"
        print graph
        print "Check the cleanup code!"
        print "Exiting"
        sys.exit()

    return graph

def makeADCvsfCgraphSepCapID(values,mean, rms, charge,histo_list = range(0,196), linkMap = {}, injectionCardMap = {},qieRange=0,shuntMult=1, verbose=False):

   
    if verbose:
        print 'Making TGraphs from histos'
    
    #print mean
    graphs = {}
    i_range=qieRange
    if shuntMult == 1:
        qierange = range(4)
    else :
        qierange = range(2) #change
    
    highCurrent = True
    
    #if i_range > 0 or shuntMult>1:
    #    highCurrent = True
    #else:
    #    highCurrent = False
   # print "histoList:", histo_list[0]
   # print "values:", values
    #lsbList = values[histo_list[0]].keys()
    #lsbList.sort()
    for ih in histo_list:
        channel = (ih % 16 + 1)        
            
    
        _charge = array("d",charge[i_range][ih][:-1])
        _chargeErr = array("d",[0 for i in range(len(charge[i_range][ih][:-1]))])
        graphs[ih] = [] 
        #print len(mean[1][14][1]),len(charge[1][14][:-1])
        for i_capID in range(4):    
            #print "the hist is :", ih  
            ADCvsfC=(TGraphErrors(len(mean[i_range][ih][i_capID]),_charge,mean[i_range][ih][i_capID],_chargeErr,rms[i_range][ih][i_capID]))
            ADCvsfC.SetNameTitle("LinADCvsfC_%i_%i_range_%i_shunt_%s_capID_%i"%(ih, channel,i_range, ("%.1f"%shuntMult).replace(".","_"),i_capID),"LinADCvsfC_%i_%i_range_%i_shunt_%.1f_capID_%i"%(ih, channel,i_range,float(shuntMult),i_capID))


            ADCvsfC = cleanGraph(ADCvsfC, i_range)

            graphs[ih].append(ADCvsfC)
         
    return graphs
