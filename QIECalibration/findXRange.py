#!/usr/bin/env python
from ROOT import *
import sys
import os
import json
import glob
import fnmatch
import time
import numpy as np
from array import array
from pprint import pprint
from collections import Counter
from rootpy.interactive import wait
from rootpy.plotting import Hist

#gROOT.SetBatch(True)
gROOT.SetStyle("Plain")

try:
    Quiet(TObject())
except NameError:
    from utils import Quiet

ranges = [0,1,2,3]

def GetKeyNames( self, dir = "" ):
        self.cd(dir)
        return [key.GetName() for key in gDirectory.GetListOfKeys()]
TFile.GetKeyNames = GetKeyNames


def findXRange(inputDir):
    xRange = {0:{'min':[],'max':[]},1:{'min':[],'max':[]},2:{'min':[],'max':[]},3:{'min':[],'max':[]}}
    fileList = []
    for root,dirnames,filenames in os.walk(os.path.join(inputDir,"Submission")):
        for filename in fnmatch.filter(filenames,'*.json'):
            fileList.append(os.path.join(root,filename))

    for fName in fileList:
        rootFile = TFile.Open(fName.replace(".json",".root").replace("70/","70/fitResults_"),'read')

        outputDir = os.path.dirname(fName)

        for gName in rootFile.GetKeyNames("LinadcVsCharge"):
            #print "%s: %s"%(fName,gName)
            tDir = rootFile.Get("LinadcVsCharge")
            graph = tDir.Get(gName)
            minEl = TMath.MinElement(graph.GetN(),graph.GetX())
            maxEl = TMath.MaxElement(graph.GetN(),graph.GetX())
            for r in ranges:
                if "range_%d"%r in gName:
                    xRange[r]['min'].append(minEl)
                    xRange[r]['max'].append(maxEl)
    avgXRange = {0:[np.array(xRange[0]['min']).mean(),np.array(xRange[0]['max']).mean()],\
                 1:[np.array(xRange[1]['min']).mean(),np.array(xRange[1]['max']).mean()],\
                 2:[np.array(xRange[2]['min']).mean(),np.array(xRange[2]['max']).mean()],\
                 3:[np.array(xRange[3]['min']).mean(),np.array(xRange[3]['max']).mean()]\
                 }
    r0min = np.array(xRange[0]['min'])
    r0max = np.array(xRange[0]['max'])
    r1min = np.array(xRange[1]['min'])
    r1max = np.array(xRange[1]['max'])
    r2min = np.array(xRange[2]['min'])
    r2max = np.array(xRange[2]['max'])
    r3min = np.array(xRange[3]['min'])
    r3max = np.array(xRange[3]['max'])

    minRange = {0:r0min,1:r1min,2:r2min,3:r3min}
    maxRange = {0:r0max,1:r1max,2:r2max,3:r3max}

    minHists = []
    maxHists = []
    c = []
    cmax = []
    for r in ranges:
        c.append(TCanvas())
        minHists.append(Hist(100,np.amin(minRange[r])-0.1*minRange[r].mean(),np.amax(minRange[r])+0.1*minRange[r].mean(),title="Minimum X Value Range %d"%r))
        minHists[-1].fill_array(minRange[r])
        minHists[-1].Draw("hist")
        c[-1].Draw()
        c[-1].SaveAs("%s.png"%minHists[-1].GetTitle())
        cmax.append(TCanvas())
        maxHists.append(Hist(100,np.amax(maxRange[r])-0.1*maxRange[r].mean(),np.amax(maxRange[r])+0.1*maxRange[r].mean(),title="Maximum X Value Range %d"%r))
        maxHists[-1].fill_array(maxRange[r])
        maxHists[-1].Draw("hist")
        cmax[-1].Draw()
        cmax[-1].SaveAs("%s.png"%maxHists[-1].GetTitle())
    wait(True)

#    h1 = Hist(100,np.amin(r0min)-0.1*r0min.mean(),np.amax(r0min)+0.1*r0min.mean(),title="Test Histogram")
#    h1.fill_array(r0min)
#    h1.Draw("hist")
#    wait(True)

if __name__ == '__main__':
    findXRange(sys.argv[1])
