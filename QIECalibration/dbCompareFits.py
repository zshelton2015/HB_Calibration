#!/usr/bin/env python

################################################################
#  Compares calibration parameters (slope,offset) from 2 runs  #
################################################################

import os,sys
from ROOT import *
from argparse import ArgumentParser
import sqlite3
from pprint import pprint
from ast import literal_eval
from glob import glob
import re
import pickle

findRunNum = re.compile(r"Run_([0-9]+)")

shunts = [1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11.5]
foundShunts = []

slopeMaxShunts = {1:0.33, 1.5:0.22,  2:0.168, 3:0.115, 4:0.085, 5:0.068,  6:0.058, 7:0.05,  8:0.044, 9:0.039, 10:0.035, 11:0.032, 11.5:0.031}
slopeMinShunts = {1:0.29, 1.5:0.185, 2:0.143, 3:0.95,  4:0.072, 5:0.0575, 6:0.048, 7:0.041, 8:0.036, 9:0.032, 10:0.029, 11:0.026, 11.5:0.025}

offsetMaxRange = {0:-0.48, 1:15,  2:100,  3:800}
offsetMinRange = {0:-0.52, 1:-20, 2:-100, 3:-800}

offsetMaxResRange = {0:0.03, 1:2,  2:2,  3:2}
offsetMinResRange = {0:-0.03, 1:-2, 2:-2, 3:-2}

parser = ArgumentParser()
parser.add_argument("-x", "--dir1", help="first input directory" )
parser.add_argument("-y", "--dir2", help="second input directory" )
parser.add_argument("-o", "--dir", dest="outDir", default="compareFits", help="output directory" )

args = parser.parse_args()

if args.dir1[-1] == "/":
    args.dir1 = args.dir1[:-1]
if args.dir2[-1] == "/":
    args.dir2 = args.dir2[:-1]
if args.outDir[-1] == "/":
    args.outDir = args.outDir[:-1]
os.system("mkdir -p %s" % args.outDir)

try:
    runNum1 = int(findRunNum.findall(args.dir1)[0])
except:
    print "Can't find run number from %s" % args.dir1
    sys.exit()

try:
    runNum2 = int(findRunNum.findall(args.dir2)[0])
except:
    print "Can't find run number from %s" % args.dir2
    sys.exit()

print ""
print '=' * 30
print "  Comparing runs %d and %d" % (runNum1, runNum2) 
print '=' * 30
print ""

# Load histoMaps
histoMap1 = {}
histoMap2 = {}

try:
    with open("%s/histoMap.txt"%args.dir1, "r") as f:
        for i,line in enumerate(f):
            if line[0] == "#": continue
            histoMap1 = dict(literal_eval(line))
except:
    print "Unable to load histoMap from file: %s" % args.dir1
    histoMap1 = None

try:
    with open("%s/histoMap.txt"%args.dir2, "r") as f:
        for i,line in enumerate(f):
            if line[0] == "#": continue
            histoMap2 = dict(literal_eval(line))
except:
    print "Unable to load histoMap from file: %s\n" % args.dir2
    histoMap2 = None

    
cards1 = {}
cards2 = {}

if histoMap1 is not None and histoMap2 is not None: 
    for h in sorted(histoMap1.keys()):
        if histoMap1[h]["UniqueID"] not in cards1.keys():
            cards1[histoMap1[h]["UniqueID"]] = {"RM":histoMap1[h]["RM"], "Slot":histoMap1[h]["Slot"]}

    for h in sorted(histoMap2.keys()):
        if histoMap2[h]["UniqueID"] not in cards2.keys():
            cards2[histoMap2[h]["UniqueID"]] = {"RM":histoMap2[h]["RM"], "Slot":histoMap2[h]["Slot"]}
    
    # Bail if runs do not contain the same cards
    if set(cards1.keys()) != set(cards2.keys()):
        print "Runs have different cards! Aborting."
        sys.exit()
    
#pprint(cards1)
#pprint(cards2)
#uidList = sorted(cards1.keys())

uidList = []
files = glob("%s/qieCal*.db" % args.dir1)
for f in files:
    uidList.append(f[f.find("s_")+2:f.find(".db")])

print "Found cards:"
for uid in uidList:
    print "%s"%uid, "\tRM %d  Slot %d" % (cards1[uid]["RM"], cards1[uid]["Slot"]) if uid in cards1 else ""
if len(cards1) == 0:
    print "RM & Slot information not available."
print ""

slopes1 = {}
slopes2 = {}
offsets1 = {}
offsets2 = {}



for uid in uidList: 
    print "Now on", uid
    slopes1[uid] = {}
    slopes2[uid] = {}
    offsets1[uid] = {}
    offsets2[uid] = {}

    db1 = sqlite3.connect("%s/qieCalibrationParameters_%s.db" % (args.dir1, uid))
    db2 = sqlite3.connect("%s/qieCalibrationParameters_%s.db" % (args.dir2, uid))
    cursor1 = db1.cursor()
    cursor2 = db2.cursor()

    for sh in shunts: 
        # Given in HW numbering (1-16)
        test1 = cursor1.execute("select slope,offset from qieshuntparams where shunt=%.1f;" % (sh,)).fetchall()
        test2 = cursor2.execute("select slope,offset from qieshuntparams where shunt=%.1f;" % (sh,)).fetchall()
        if len(test1) == 0 or len(test2) == 0:
            continue
        if sh not in foundShunts:
            foundShunts.append(sh)
        slopes1[uid][sh] = {}    
        slopes2[uid][sh] = {}    
        offsets1[uid][sh]  = {}
        offsets2[uid][sh]  = {}
        
        for r in xrange(4):
            if sh > 1 and r > 1: continue
            limits1 = cursor1.execute("select max(slope),min(slope),max(offset),min(offset) from qieshuntparams where range=%i and shunt=%.1f;" % (r,sh)).fetchall()
            limits2 = cursor2.execute("select max(slope),min(slope),max(offset),min(offset) from qieshuntparams where range=%i and shunt=%.1f;" % (r,sh)).fetchall()
            slopes1[uid][sh][r] = {}
            slopes2[uid][sh][r] = {}
            offsets1[uid][sh][r] = {}
            offsets2[uid][sh][r] = {}
            
            smax1, smin1, omax1, omin1 = limits1[0]
            smax2, smin2, omax2, omin2 = limits2[0]
            slopes1[uid][sh][r]["max"] = smax1
            slopes1[uid][sh][r]["min"] = smin1
            slopes2[uid][sh][r]["max"] = smax2
            slopes2[uid][sh][r]["min"] = smin2
            
            offsets1[uid][sh][r]["max"] = omax1
            offsets1[uid][sh][r]["min"] = omin1
            offsets2[uid][sh][r]["max"] = omax2
            offsets2[uid][sh][r]["min"] = omin2


            for qie in xrange(1,17):
                slopes1[uid][sh][r][qie] = {}
                slopes2[uid][sh][r][qie] = {}
                offsets1[uid][sh][r][qie] = {}
                offsets2[uid][sh][r][qie] = {}
                
                for capID in xrange(4):
                    vals1 = cursor1.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f and qie=%i and capid=%i;" % (r,sh,qie,capID)).fetchall()
                    vals2 = cursor2.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f and qie=%i and capid=%i;" % (r,sh,qie,capID)).fetchall()
                    if len(vals1) != 1:
                        print "vals1 has length", len(vals1)
                    if len(vals2) != 1:
                        print "vals2 has length", len(vals2)
                    
                    slopes1[uid][sh][r][qie][capID] = vals1[0][0]
                    offsets1[uid][sh][r][qie][capID] = vals1[0][1] 
                    slopes2[uid][sh][r][qie][capID] = vals2[0][0]
                    offsets2[uid][sh][r][qie][capID] = vals2[0][1]
    cursor1.close()
    db1.close()
    cursor2.close()
    db2.close()


print "\nFound shunts: ",
for sh in foundShunts: print "%d " % sh if int(sh) == sh else "%.1f " % sh,
print "\n"

h2D_slopes = {}
h2D_offsets = {}

maxslope = {}
minslope = {}
maxoffset = {}
minoffset = {}

maxresSlope = {}
minresSlope = {}
maxresOffset = {}
minresOffset = {}

# Residuals for slopes/offsets
# Slope: (norm) res = (val1 - val2)/(val1)
# Offset: res = (val1 - val2)
res_slopes = {}
res_offsets = {}
res_slopes_all = {}
res_offsets_all = {}

h2D_slopes_all = {}
h2D_offsets_all = {}

h2D_slope1_vs_qie = {}
h2D_slope2_vs_qie = {}
h2D_slope1_vs_qie_all = {}
h2D_slope2_vs_qie_all = {}


# Deteremine min/max for slopes,offsets
for uid in uidList: 
    maxslope[uid] = {}
    minslope[uid] = {}
    maxoffset[uid] = {}
    minoffset[uid] = {}
    
    maxresSlope[uid] = {}
    minresSlope[uid] = {}
    maxresOffset[uid] = {}
    minresOffset[uid] = {}
    for sh in foundShunts:
        maxslope[uid][sh] = {}
        minslope[uid][sh] = {}
        maxoffset[uid][sh] = {}
        minoffset[uid][sh] = {}
    
        maxresSlope[uid][sh] = {}
        minresSlope[uid][sh] = {}
        maxresOffset[uid][sh] = {}
        minresOffset[uid][sh] = {}
        
        for r in xrange(4):
            if sh > 1 and r > 1: continue
            maxslope[uid][sh][r] = max( max(slopes1[uid][sh][r]["max"],slopes2[uid][sh][r]["max"])*1.01, slopeMaxShunts[sh])
            minslope[uid][sh][r] = min( min(slopes1[uid][sh][r]["min"],slopes2[uid][sh][r]["min"])*0.99, slopeMinShunts[sh])
            maxoffset[uid][sh][r] = max( max(offsets1[uid][sh][r]["max"],offsets2[uid][sh][r]["max"])*1.01, offsetMaxRange[r])
            minoffset[uid][sh][r] = min( min(offsets1[uid][sh][r]["min"],offsets2[uid][sh][r]["min"])*0.99, offsetMinRange[r])
    
            maxresSlope[uid][sh][r] = 0.03 
            minresSlope[uid][sh][r] = -0.03
            maxresOffset[uid][sh][r] = offsetMaxResRange[r] 
            minresOffset[uid][sh][r] = offsetMinResRange[r]
            #maxresOffset[uid][sh][r] = 0.03
            #minresOffset[uid][sh][r] = -0.03
            
            for qie in xrange(1,17):
                for capID in xrange(4):
                    maxresSlope[uid][sh][r] = max( (slopes1[uid][sh][r][qie][capID] - slopes2[uid][sh][r][qie][capID])/slopes1[uid][sh][r][qie][capID] *1.3, maxresSlope[uid][sh][r])
                    minresSlope[uid][sh][r] = min( (slopes1[uid][sh][r][qie][capID] - slopes2[uid][sh][r][qie][capID])/slopes1[uid][sh][r][qie][capID] *0.7, minresSlope[uid][sh][r])
                    maxresOffset[uid][sh][r] = max( (offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID])/8**r * 1.3, maxresOffset[uid][sh][r])
                    minresOffset[uid][sh][r] = min( (offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID])/8**r * 0.7, minresOffset[uid][sh][r])
                    #maxresOffset[uid][sh][r] = max( (offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID])/offsets1[uid][sh][r][qie][capID] *1.3, maxresOffset[uid][sh][r])
                    #minresOffset[uid][sh][r] = min( (offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID])/offsets1[uid][sh][r][qie][capID] *0.7, minresOffset[uid][sh][r])


maxslope["all"] = {} 
minslope["all"] = {}
maxoffset["all"] = {}
minoffset["all"] = {}

maxresSlope["all"] = {} 
minresSlope["all"] = {}
maxresOffset["all"] = {}
minresOffset["all"] = {}

for sh in foundShunts:
    maxslope["all"][sh] = {} 
    minslope["all"][sh] = {}
    maxoffset["all"][sh] = {}
    minoffset["all"][sh] = {}

    maxresSlope["all"][sh] = {} 
    minresSlope["all"][sh] = {}
    maxresOffset["all"][sh] = {}
    minresOffset["all"][sh] = {}
    
    for r in xrange(4):
        if sh > 1 and r > 1: continue
        maxslope["all"][sh][r] = max( [maxslope[uid][sh][r] for uid in uidList] )
        minslope["all"][sh][r] = min( [minslope[uid][sh][r] for uid in uidList] )
        maxoffset["all"][sh][r] = max( [maxoffset[uid][sh][r] for uid in uidList] )
        minoffset["all"][sh][r] = min( [minoffset[uid][sh][r] for uid in uidList] )

        maxresSlope["all"][sh][r] = max( [maxresSlope[uid][sh][r] for uid in uidList] )
        minresSlope["all"][sh][r] = min( [minresSlope[uid][sh][r] for uid in uidList] )
        maxresOffset["all"][sh][r] = max( [maxresOffset[uid][sh][r] for uid in uidList] )
        minresOffset["all"][sh][r] = min( [minresOffset[uid][sh][r] for uid in uidList] )


for uid in uidList:
    print "Plotting card %s" % uid
    h2D_slopes[uid] = {}
    h2D_offsets[uid] = {}
    h2D_slope1_vs_qie[uid] = {}
    h2D_slope2_vs_qie[uid] = {}

    res_slopes[uid] = {}
    res_offsets[uid] = {}

    for sh in foundShunts:
        shstr = str(sh).replace(".","_")
        h2D_slopes[uid][sh] = {}
        h2D_offsets[uid][sh] = {}
        h2D_slope1_vs_qie[uid][sh] = {}
        h2D_slope2_vs_qie[uid][sh] = {}
    
        res_slopes[uid][sh] = {}
        res_offsets[uid][sh] = {}

        if sh not in h2D_slopes_all.keys():
            #print "Initializing total plots for shunt %s" % sh
            h2D_slopes_all[sh] = {}
            h2D_offsets_all[sh] = {}
            h2D_slope1_vs_qie_all[sh] = {}
            h2D_slope2_vs_qie_all[sh] = {}
    
            res_slopes_all[sh] = {}
            res_offsets_all[sh] = {}
        for r in xrange(4):
            if sh > 1 and r > 1: continue
            h2D_slopes[uid][sh][r] = {}
            h2D_offsets[uid][sh][r] = {}
            h2D_slope1_vs_qie[uid][sh][r] = {}
            h2D_slope2_vs_qie[uid][sh][r] = {}
            
            res_slopes[uid][sh][r] = {}
            res_offsets[uid][sh][r] = {}

            if r not in h2D_slopes_all[sh].keys():
                #print "Initializing total plots for shunt %s range %d" % (sh,r)
                h2D_slopes_all[sh][r] =  TH2D("slopes_shunt_%s_range_%d" % (shstr,r), "Slopes  Shunt %.1f Range %d" % (sh,r), 100, minslope["all"][sh][r], maxslope["all"][sh][r], 100, minslope["all"][sh][r], maxslope["all"][sh][r])
                h2D_offsets_all[sh][r] =  TH2D("offsets_shunt_%s_range_%d" % (shstr,r), "Offsets  Shunt %.1f Range %d" % (sh,r), 100, minoffset["all"][sh][r], maxoffset["all"][sh][r], 100, minoffset["all"][sh][r], maxoffset["all"][sh][r])
                h2D_slopes_all[sh][r].GetXaxis().SetTitle("Run %d Slopes" % runNum1) 
                h2D_slopes_all[sh][r].GetYaxis().SetTitle("Run %d Slopes" % runNum2) 
                h2D_offsets_all[sh][r].GetXaxis().SetTitle("Run %d Offsets" % runNum1) 
                h2D_offsets_all[sh][r].GetYaxis().SetTitle("Run %d Offsets" % runNum2) 

                h2D_slopes_all[sh][r].SetDirectory(0)
                h2D_offsets_all[sh][r].SetDirectory(0)

                h2D_slope1_vs_qie_all[sh][r] = TH2D("slope1_vs_qie_shunt_%s_range_%d" % (shstr,r), "Run %d  Slope vs QIE  Shunt %.1f Range %d" % (runNum1,sh,r), 16, 0.5, 16.5, 100, minslope["all"][sh][r], maxslope["all"][sh][r])
                h2D_slope2_vs_qie_all[sh][r] = TH2D("slope2_vs_qie_shunt_%s_range_%d" % (shstr,r), "Run %d  Slope vs QIE  Shunt %.1f Range %d" % (runNum2,sh,r), 16, 0.5, 16.5, 100, minslope["all"][sh][r], maxslope["all"][sh][r])
                h2D_slope1_vs_qie_all[sh][r].GetXaxis().SetTitle("QIE Channel")
                h2D_slope1_vs_qie_all[sh][r].GetYaxis().SetTitle("Run %d Slopes" % runNum1)
                h2D_slope2_vs_qie_all[sh][r].GetXaxis().SetTitle("QIE Channel")
                h2D_slope2_vs_qie_all[sh][r].GetYaxis().SetTitle("Run %d Slopes" % runNum2)
                
                h2D_slope1_vs_qie_all[sh][r].SetDirectory(0)
                h2D_slope2_vs_qie_all[sh][r].SetDirectory(0)
                
                res_slopes_all[sh][r] = TH1D("res_slopes_shunt_%s_range_%d" % (shstr,r), "Normalized Residual Slopes  Shunt %.1f Range %d" % (sh,r), 100, minresSlope['all'][sh][r], maxresSlope['all'][sh][r])
                res_offsets_all[sh][r] = TH1D("res_offsets_shunt_%s_range_%d" % (shstr,r), "Normalized Residual Offsets  Shunt %.1f Range %d" % (sh,r), 100, minresOffset['all'][sh][r], maxresOffset['all'][sh][r]) 
                res_slopes_all[sh][r].GetXaxis().SetTitle("(Slope1 - Slope2)/Slope1") 
                res_slopes_all[sh][r].GetYaxis().SetTitle("QIE Channels")
                res_offsets_all[sh][r].GetXaxis().SetTitle("Offset1 - Offset2  [ADC]" if r == 0 else "(Offset1 - Offset2) / %d  [ADC]" % 8**r) 
                #res_offsets_all[sh][r].GetXaxis().SetTitle("(Offset1 - Offset2)/Offset1") 
                res_offsets_all[sh][r].GetYaxis().SetTitle("QIE Channels")
                
                res_slopes_all[sh][r].SetDirectory(0)
                res_offsets_all[sh][r].SetDirectory(0)



            h2D_slope1_vs_qie[uid][sh][r] = TH2D("%s_slope1_vs_qie_shunt_%s_range_%d" % (uid, shstr,r), "Run %d  %s  Slope vs QIE  Shunt %.1f Range %d" % (runNum1,uid,sh,r), 16, 0.5, 16.5, 100, minslope[uid][sh][r], maxslope[uid][sh][r])
            h2D_slope2_vs_qie[uid][sh][r] = TH2D("%s_slope2_vs_qie_shunt_%s_range_%d" % (uid, shstr,r), "Run %d  %s  Slope vs QIE  Shunt %.1f Range %d" % (runNum2,uid,sh,r), 16, 0.5, 16.5, 100, minslope[uid][sh][r], maxslope[uid][sh][r])
            h2D_slope1_vs_qie[uid][sh][r].SetDirectory(0)
            h2D_slope2_vs_qie[uid][sh][r].SetDirectory(0)
            
            h2D_slope1_vs_qie[uid][sh][r].GetXaxis().SetTitle("QIE Channel")
            h2D_slope1_vs_qie[uid][sh][r].GetYaxis().SetTitle("Run %d Slopes" % runNum1)
            h2D_slope2_vs_qie[uid][sh][r].GetXaxis().SetTitle("QIE Channel")
            h2D_slope2_vs_qie[uid][sh][r].GetYaxis().SetTitle("Run %d Slopes" % runNum2)
            

            h2D_slopes[uid][sh][r]["total"] = TH2D("%s_slopes_shunt_%s_range_%d" % (uid,shstr,r), "%s  Slopes  Shunt %.1f Range %d" % (uid,sh,r), 100, minslope[uid][sh][r], maxslope[uid][sh][r], 100, minslope[uid][sh][r], maxslope[uid][sh][r]) 
            h2D_offsets[uid][sh][r]["total"] = TH2D("%s_offsets_shunt_%s_range_%d" % (uid,shstr,r), "%s   Offsets  Shunt %.1f Range %d" % (uid,sh,r), 100, minoffset[uid][sh][r], maxoffset[uid][sh][r], 100, minoffset[uid][sh][r], maxoffset[uid][sh][r]) 
            
            h2D_slopes[uid][sh][r]["total"].SetDirectory(0) 
            h2D_offsets[uid][sh][r]["total"].SetDirectory(0)
            
            h2D_slopes[uid][sh][r]["total"].GetXaxis().SetTitle("Run %d Slopes" % runNum1)
            h2D_slopes[uid][sh][r]["total"].GetYaxis().SetTitle("Run %d Slopes" % runNum2)
            h2D_offsets[uid][sh][r]["total"].GetXaxis().SetTitle("Run %d Offsets" % runNum1)
            h2D_offsets[uid][sh][r]["total"].GetYaxis().SetTitle("Run %d Offsets" % runNum2)


            res_slopes[uid][sh][r] = TH1D("%s_res_slopes_shunt_%s_range_%d" % (uid,shstr,r), "%s  Normalized Residual Slopes  Shunt %.1f Range %d" % (uid,sh,r), 100, minresSlope[uid][sh][r], maxresSlope[uid][sh][r]) 
            res_offsets[uid][sh][r] = TH1D("%s_res_offsets_shunt_%s_range_%d" % (uid,shstr,r), "%s  Normalized Residual Offsets  Shunt %.1f Range %d" % (uid,sh,r), 100, minresOffset[uid][sh][r], maxresOffset[uid][sh][r]) 
            res_slopes[uid][sh][r].GetXaxis().SetTitle("(Slope1 - Slope2)/Slope1") 
            res_slopes[uid][sh][r].GetYaxis().SetTitle("QIE Channels")
            res_offsets[uid][sh][r].GetXaxis().SetTitle("Offset1 - Offset2  [ADC]" if r == 0 else "(Offset1 - Offset2) / %d  [ADC]" % 8**r)
            #res_offsets[uid][sh][r].GetXaxis().SetTitle("(Offset1 - Offset2)/Offset1") 
            res_offsets[uid][sh][r].GetYaxis().SetTitle("QIE Channels")
            
            res_slopes[uid][sh][r].SetDirectory(0)
            res_offsets[uid][sh][r].SetDirectory(0)


            for qie in xrange(1,17):
                h2D_slopes[uid][sh][r][qie] = TH2D("%s_QIE_%d_slopes_shunt_%s_range_%d" % (uid,qie,shstr,r), "%s  QIE %d  Slopes  Shunt %.1f Range %d" % (uid,qie,sh,r), 100, minslope[uid][sh][r], maxslope[uid][sh][r], 100, minslope[uid][sh][r], maxslope[uid][sh][r]) 
                h2D_offsets[uid][sh][r][qie] = TH2D("%s_QIE_%d_offsets_shunt_%s_range_%d" % (uid,qie,shstr,r), "%s  QIE %d  Offsets  Shunt %.1f Range %d" % (uid,qie,sh,r), 100, minoffset[uid][sh][r], maxoffset[uid][sh][r], 100, minoffset[uid][sh][r], maxoffset[uid][sh][r]) 
                
                h2D_slopes[uid][sh][r][qie].SetDirectory(0)
                h2D_offsets[uid][sh][r][qie].SetDirectory(0)
                
                h2D_slopes[uid][sh][r][qie].GetXaxis().SetTitle("Run %d Slopes" % runNum1)
                h2D_slopes[uid][sh][r][qie].GetYaxis().SetTitle("Run %d Slopes" % runNum2)
                h2D_offsets[uid][sh][r][qie].GetXaxis().SetTitle("Run %d Offsets" % runNum1)
                h2D_offsets[uid][sh][r][qie].GetYaxis().SetTitle("Run %d Offsets" % runNum2)
                
                for capID in xrange(4):
                    #if sh == 1 and r == 1 and qie == 15 and capID == 3:
                     #   print slopes1[uid][sh][r][qie][capID], slopes2[uid][sh][r][qie][capID]
                    h2D_slopes_all[sh][r].Fill(slopes1[uid][sh][r][qie][capID], slopes2[uid][sh][r][qie][capID])
                    h2D_offsets_all[sh][r].Fill(offsets1[uid][sh][r][qie][capID], offsets2[uid][sh][r][qie][capID])

                    h2D_slopes[uid][sh][r]["total"].Fill(slopes1[uid][sh][r][qie][capID], slopes2[uid][sh][r][qie][capID])
                    h2D_slopes[uid][sh][r][qie].Fill(slopes1[uid][sh][r][qie][capID], slopes2[uid][sh][r][qie][capID])
                    h2D_offsets[uid][sh][r]["total"].Fill(offsets1[uid][sh][r][qie][capID], offsets2[uid][sh][r][qie][capID])
                    h2D_offsets[uid][sh][r][qie].Fill(offsets1[uid][sh][r][qie][capID], offsets2[uid][sh][r][qie][capID])

                    h2D_slope1_vs_qie_all[sh][r].Fill(qie, slopes1[uid][sh][r][qie][capID])
                    h2D_slope2_vs_qie_all[sh][r].Fill(qie, slopes2[uid][sh][r][qie][capID])
                    h2D_slope1_vs_qie[uid][sh][r].Fill(qie, slopes1[uid][sh][r][qie][capID])
                    h2D_slope2_vs_qie[uid][sh][r].Fill(qie, slopes2[uid][sh][r][qie][capID])

                    res_slopes_all[sh][r].Fill((slopes1[uid][sh][r][qie][capID] - slopes2[uid][sh][r][qie][capID])/slopes1[uid][sh][r][qie][capID])
                    res_offsets_all[sh][r].Fill((offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID]) / 8**r)
                    #res_offsets_all[sh][r].Fill((offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID])/offsets1[uid][sh][r][qie][capID])
                    
                    res_slopes[uid][sh][r].Fill((slopes1[uid][sh][r][qie][capID] - slopes2[uid][sh][r][qie][capID])/slopes1[uid][sh][r][qie][capID])
                    res_offsets[uid][sh][r].Fill((offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID]) / 8**r)
                    #res_offsets[uid][sh][r].Fill((offsets1[uid][sh][r][qie][capID] - offsets2[uid][sh][r][qie][capID])/offsets1[uid][sh][r][qie][capID])

"""
with open("%s/debug.p"%args.outDir, "wb") as f:
    pickle.dump(h2D_slopes_all, f)
    pickle.dump(h2D_offsets_all, f)
    pickle.dump(h2D_slopes, f)
    pickle.dump(h2D_offsets, f)
    pickle.dump(slopes1, f)
    pickle.dump(slopes2, f)
    pickle.dump(offsets1, f)
    pickle.dump(offsets2, f)
"""

gROOT.SetBatch(True)
outF = TFile.Open("%s/%s.root" % (args.outDir, os.path.basename(args.outDir)), "recreate")

print "\nSaving results to %s/%s.root" % (args.outDir, os.path.basename(args.outDir))

"""
for sh in foundShunts:
    for r in xrange(4):
        if sh > 1 and r > 1: continue
        #outF.cd("")
        #print "Saving Shunt %.1f Range %d" % (sh,r)
        h2D_slopes_all[sh][r].Write()
        h2D_offsets_all[sh][r].Write()
        for uid in uidList:
            #if sh == foundShunts[0] and r == 0 and uid == uidList[0]:
            #    print "I should only execute once"
            #    outF.mkdir(uid)
            #outF.cd(uid)
            h2D_slopes[uid][sh][r]["total"].Write()
            h2D_offsets[uid][sh][r]["total"].Write()
            for qie in xrange(1,17):
            #    if sh == foundShunts[0] and r == 0 and uid == uidList[0] and qie == 1:
            #        outF.mkdir("%s/QIE_%d" % (uid,qie))
            #    outF.cd("%s/QIE_%d" % (uid,qie))
                h2D_slopes[uid][sh][r][qie].Write()
                h2D_offsets[uid][sh][r][qie].Write()
"""

for sh in foundShunts:
    for r in xrange(4):
        if sh > 1 and r > 1: continue
        h2D_slopes_all[sh][r].Write()
        h2D_offsets_all[sh][r].Write()
        h2D_slope1_vs_qie_all[sh][r].Write()
        h2D_slope2_vs_qie_all[sh][r].Write()
        res_slopes_all[sh][r].Write()
        res_offsets_all[sh][r].Write()

for uid in uidList:
    d = outF.mkdir(uid)
    outF.cd(uid)
    for qie in xrange(1,17):
        d.mkdir("QIE_%d" % (qie))

    #d.mkdir("Run_%d_slope_vs_qie" % runNum1)
    #d.mkdir("Run_%d_slope_vs_qie" % runNum2)


for uid in uidList:
    for sh in foundShunts:
        for r in xrange(4):
            if sh > 1 and r > 1: continue
            outF.cd(uid)
            h2D_slopes[uid][sh][r]["total"].Write()
            h2D_offsets[uid][sh][r]["total"].Write()
            #outF.cd("%s/Run_%d_slope_vs_qie" % runNum1)
            h2D_slope1_vs_qie[uid][sh][r].Write()
            #outF.cd("%s/Run_%d_slope_vs_qie" % runNum2)
            h2D_slope2_vs_qie[uid][sh][r].Write()
            res_slopes[uid][sh][r].Write()
            res_offsets[uid][sh][r].Write()
            for qie in xrange(1,17):
                outF.cd()
                outF.cd("%s/QIE_%d" % (uid,qie))
                h2D_slopes[uid][sh][r][qie].Write()
                h2D_offsets[uid][sh][r][qie].Write()
            
outF.Close()
print "Done!\n"
