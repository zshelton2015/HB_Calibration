#!/usr/bin/env python
#Author: Zach Shelton
#Date:8-2-2018
#Purpose: Take all passing cards from QIE Calibration and output summary plots of calibration data
import sqlite3
import pprint
import os
import sys
from MergeDatabases import MergeDatabases
from selectionCuts import *
from utils import Quiet
from passedCards import dblist
if not os.path.exists("Summary_Of_Calibration"):
    os.makedirs("Summary_Of_Calibration")
rootout = TFile("Summary_Of_Calibration/TotalAnalysis.root", "recreate")
idlist = []
bins = [0,1,2,3]
shunts = [1,1.5,2,3,4,5,6,7,8,9,10,11,11.5]
shuntcount = [0,1,2,3,4,5,6,7,8,9,10,11,12]
#c is a dictionary of list of each canvas for each shunt and range
c = {0:[],1:[],2:[],3:[]}
histshunt = {0:[],1:[],2:[],3:[]}
histoffset = {0:[],1:[],2:[],3:[]}
#TODO IMPORT LIST IN SYSARGRV[1]
for ra in bins:
    for ind in shuntcount:
        if (r == 2 or r == 3) and (sh != 1):
            continue
        sh = shunts[ind]
        r = ra
        c[r].append(TCanvas("Shunt %.1f  -  Range %i" % (sh, r), "histo"))
        c[r][-1].Divide(2,1)
        c[r][-1].cd(1)
        maximums = failureconds[shunt][0]-failureconds[shunt][0]*.3
        minimums = failureconds[shunt][1]+failureconds[shunt][1]*.3
        #Create Histograms for the shunt slopes
        histshunt[r].append(TH1D("SLOPE_Sh:_%.1f_RANGE_r:_%d" %(sh,r),"SLOPE Sh: %.1f RANGE r: %d" %(sh,r), 100, minimums, maximums))
        #histshunt[-1].SetTitle("SLOPE SH: %.1f "%(sh))
        histshunt[r][-1].GetXaxis().SetTitle("Slope")
        histshunt[r][-1].GetYaxis().SetTitle("Frequency")
        gPad.SetLogy(1)
        maximumo  = -1*failurecondo[ra]-failurecondo[ra]*.3
        minimumo  = failurecondo[ra]+failurecondo[ra]*..3
        c[r].cd(2)
        histoffset[r].append(TH1D("OFFSET Sh: %.1f - R: %i" %(sh, r),"Shunt %.1f - Range %d" %(sh, r), 40, minimumo, maximumo))
        histoffset[r][-1].SetTitle("OFFSET SH: %.1f R: %d"%(sh,r))
        histoffset[r][-1].GetXaxis().SetTitle("Offset")
        histoffset[r][-1].GetYaxis().SetTitle("Frequency")
        gPad.SetLogy(1)
for file in dblist:
    xyz1234 = sqlite3.connect("%s"%(file))
    cursor = xyz1234.cursor()
    # Set digit limit on histogram
    TGaxis.SetMaxDigits(3)
    for ra in bins:
        for ind in shuntcount:
            if (r == 2 or r == 3) and (sh != 1):
                continue
            sh = shunts[shuntcount]
            r = ra
            # Fetch the values of slope and offset for the corresponding shunt and range
            # values = cursor.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f ;" % (r, sh)).fetchall()
            values = cursor.execute("select slope, offset from qieshuntparams as p where range = %i and shunt = %.1f;"%(r,sh)).fetchall()
            for val in values:
                try:
                    slope, offset = val
                except:
                    print val
                c[r][ind].cd(1)
                histshunt[r][ind].Fill(slope)
                c[r][ind].cd(2)
                histoffset[r][ind].Fill(offset)
            # Write the histograms to the file, saving them for later
            # histshunt[-1].Draw()
            # histoffset[-1].Draw()
            # c2[-1].Write()
            c[r][ind].Update()
            #c[-1].SaveAs("data/%s/Run_%s/SummaryPlots/ImagesOutput/CARD_%s_SHUNT_%s_RANGE_%i.png"%(date, run, name, str(sh).replace(".",""), r))
            if(images):
                c[-1].Print("%s/SummaryPlots/TotalOutput/Total_SHUNT_%s_RANGE_%i.png"%(indir, str(sh).replace(".",""), r))
for ra in bins:
    for ind in shuntcount:
        if (r == 2 or r == 3) and (sh != 1):
            continue
        c[r][ind].Write()
rootout.close()
print "Total Plots Shunt %.1f Range %d Finished"%(sh,r)
