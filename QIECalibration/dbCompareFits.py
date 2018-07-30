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

qieLocation = {1:"back", 2:"back", 3:"back", 4:"back", 
               5:"front", 6:"front", 7:"front", 8:"front",
               9:"back", 10:"back", 11:"back", 12:"back",
               13:"front", 14:"front", 15:"front", 16:"front"}


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


shunt_factor_1 = {}
shunt_factor_2 = {}


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
            maxslope[uid][sh][r] = max( max(slopes1[uid][sh][r]["max"],slopes2[uid][sh][r]["max"])*1.03, slopeMaxShunts[sh])
            minslope[uid][sh][r] = min( min(slopes1[uid][sh][r]["min"],slopes2[uid][sh][r]["min"])*0.97, slopeMinShunts[sh])
            if r > 0:
                maxoffset[uid][sh][r] = max( max(offsets1[uid][sh][r]["max"],offsets2[uid][sh][r]["max"])*1.03, offsetMaxRange[r])
                minoffset[uid][sh][r] = min( min(offsets1[uid][sh][r]["min"],offsets2[uid][sh][r]["min"])*0.97, offsetMinRange[r])
            else:
                maxoffset[uid][sh][r] = max( max(offsets1[uid][sh][r]["max"],offsets2[uid][sh][r]["max"])*0.97, offsetMaxRange[r])
                minoffset[uid][sh][r] = min( min(offsets1[uid][sh][r]["min"],offsets2[uid][sh][r]["min"])*1.03, offsetMinRange[r])
                
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

    shunt_factor_1[uid] = {}
    shunt_factor_2[uid] = {}
    shunt_factor_1[uid]["front"] = {}
    shunt_factor_2[uid]["front"] = {}
    shunt_factor_1[uid]["back"] = {}
    shunt_factor_2[uid]["back"] = {}
    shunt_factor_1[uid]["total"] = {}
    shunt_factor_2[uid]["total"] = {}
    shunt_factor_1["all"] = {}
    shunt_factor_2["all"] = {}
    shunt_factor_1["all"]["front"] = {}
    shunt_factor_2["all"]["front"] = {}
    shunt_factor_1["all"]["back"] = {}
    shunt_factor_2["all"]["back"] = {}
    shunt_factor_1["all"]["total"] = {}
    shunt_factor_2["all"]["total"] = {}



    res_slopes[uid] = {}
    res_offsets[uid] = {}

    for sh in foundShunts:
        shstr = str(sh).replace(".","_")
        h2D_slopes[uid][sh] = {}
        h2D_offsets[uid][sh] = {}
        h2D_slope1_vs_qie[uid][sh] = {}
        h2D_slope2_vs_qie[uid][sh] = {}
    
        shunt_factor_1[uid]["front"][sh] = {}
        shunt_factor_1[uid]["back"][sh] = {}
        shunt_factor_1[uid]["total"][sh] = {}
        shunt_factor_2[uid]["front"][sh] = {}
        shunt_factor_2[uid]["back"][sh] = {}
        shunt_factor_2[uid]["total"][sh] = {}
        shunt_factor_1["all"]["front"][sh] = {}
        shunt_factor_1["all"]["back"][sh] = {}
        shunt_factor_1["all"]["total"][sh] = {}
        shunt_factor_2["all"]["front"][sh] = {}
        shunt_factor_2["all"]["back"][sh] = {}
        shunt_factor_2["all"]["total"][sh] = {}


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
            
            shunt_factor_1[uid]["total"][sh][r] = TH1D("%s_shunt_factor_1_shunt_%s_range_%d" % (uid, shstr, r), "Run %d  %s  Shunt Factor  Shunt %.1f Range %d" % (runNum1,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_1[uid]["front"][sh][r] = TH1D("%s_shunt_factor_1_front_shunt_%s_range_%d" % (uid, shstr, r), "Run %d  %s  Shunt Factor  Front QIEs  Shunt %.1f Range %d" % (runNum1,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_1[uid]["back"][sh][r] = TH1D("%s_shunt_factor_1_back_shunt_%s_range_%d" % (uid, shstr, r), "Run %d  %s  Shunt Factor  Back QIEs  Shunt %.1f Range %d" % (runNum1,uid,sh,r), 100, sh*0.9, sh*1.05)
            
            shunt_factor_2[uid]["total"][sh][r] = TH1D("%s_shunt_factor_2_shunt_%s_range_%d" % (uid, shstr, r), "Run %d  %s  Shunt Factor  Shunt %.1f Range %d" % (runNum2,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_2[uid]["front"][sh][r] = TH1D("%s_shunt_factor_2_front_shunt_%s_range_%d" % (uid, shstr, r), "Run %d  %s  Shunt Factor  Front QIEs  Shunt %.1f Range %d" % (runNum2,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_2[uid]["back"][sh][r] = TH1D("%s_shunt_factor_2_back_shunt_%s_range_%d" % (uid, shstr, r), "Run %d  %s  Shunt Factor  Back QIEs  Shunt %.1f Range %d" % (runNum2,uid,sh,r), 100, sh*0.9, sh*1.05)
            
            shunt_factor_1["all"]["total"][sh][r] = TH1D("shunt_factor_1_shunt_%s_range_%d" % (shstr, r), "Run %d  %s  Shunt Factor  Shunt %.1f Range %d" % (runNum1,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_1["all"]["front"][sh][r] = TH1D("shunt_factor_1_front_shunt_%s_range_%d" % (shstr, r), "Run %d  %s  Shunt Factor  Front QIEs  Shunt %.1f Range %d" % (runNum1,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_1["all"]["back"][sh][r] = TH1D("shunt_factor_1_back_shunt_%s_range_%d" % (shstr, r), "Run %d  %s  Shunt Factor  Back QIEs  Shunt %.1f Range %d" % (runNum1,uid,sh,r), 100, sh*0.9, sh*1.05)
            
            shunt_factor_2["all"]["total"][sh][r] = TH1D("shunt_factor_2_shunt_%s_range_%d" % (shstr, r), "Run %d  %s  Shunt Factor  Shunt %.1f Range %d" % (runNum2,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_2["all"]["front"][sh][r] = TH1D("shunt_factor_2_front_shunt_%s_range_%d" % (shstr, r), "Run %d  %s  Shunt Factor  Front QIEs  Shunt %.1f Range %d" % (runNum2,uid,sh,r), 100, sh*0.9, sh*1.05)
            shunt_factor_2["all"]["back"][sh][r] = TH1D("shunt_factor_2_back_shunt_%s_range_%d" % (shstr, r), "Run %d  %s  Shunt Factor  Back QIEs  Shunt %.1f Range %d" % (runNum2,uid,sh,r), 100, sh*0.9, sh*1.05)
            

            shunt_factor_1[uid]["total"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_1[uid]["total"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_1[uid]["front"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_1[uid]["front"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_1[uid]["front"][sh][r].SetLineColor(kRed)
            shunt_factor_1[uid]["front"][sh][r].SetLineWidth(2.0)
            shunt_factor_1[uid]["back"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_1[uid]["back"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_1[uid]["back"][sh][r].SetLineColor(kBlue)
            shunt_factor_1[uid]["back"][sh][r].SetLineWidth(2.0)

            shunt_factor_2[uid]["total"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_2[uid]["total"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_2[uid]["front"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_2[uid]["front"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_2[uid]["front"][sh][r].SetLineColor(kRed)
            shunt_factor_2[uid]["front"][sh][r].SetLineWidth(2.0)
            shunt_factor_2[uid]["back"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_2[uid]["back"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_2[uid]["back"][sh][r].SetLineColor(kBlue)
            shunt_factor_2[uid]["back"][sh][r].SetLineWidth(2.0)
            
            
            shunt_factor_1["all"]["total"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_1["all"]["total"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_1["all"]["front"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_1["all"]["front"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_1["all"]["front"][sh][r].SetLineColor(kRed)
            shunt_factor_1["all"]["front"][sh][r].SetLineWidth(2.0)
            shunt_factor_1["all"]["back"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_1["all"]["back"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_1["all"]["back"][sh][r].SetLineColor(kBlue)
            shunt_factor_1["all"]["back"][sh][r].SetLineWidth(2.0)

            shunt_factor_2["all"]["total"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_2["all"]["total"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_2["all"]["front"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_2["all"]["front"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_2["all"]["front"][sh][r].SetLineColor(kRed)
            shunt_factor_2["all"]["front"][sh][r].SetLineWidth(2.0)
            shunt_factor_2["all"]["back"][sh][r].GetXaxis().SetTitle("Shunt Factor")
            shunt_factor_2["all"]["back"][sh][r].GetYaxis().SetTitle("QIE Channels")
            shunt_factor_2["all"]["back"][sh][r].SetLineColor(kBlue)
            shunt_factor_2["all"]["back"][sh][r].SetLineWidth(2.0)
            


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

for uid in uidList:
    for sh in foundShunts:
        if sh < 1.3: continue
        for r in xrange(4):
            if sh > 1 and r > 1: continue
            for qie in xrange(1,17):
                for capID in xrange(4):
                    shunt_factor_1[uid]["total"][sh][r].Fill(slopes1[uid][1.0][r][qie][capID] / slopes1[uid][sh][r][qie][capID])
                    shunt_factor_1[uid][qieLocation[qie]][sh][r].Fill(slopes1[uid][1.0][r][qie][capID] / slopes1[uid][sh][r][qie][capID])
                    shunt_factor_1["all"]["total"][sh][r].Fill(slopes1[uid][1.0][r][qie][capID] / slopes1[uid][sh][r][qie][capID])
                    shunt_factor_1["all"][qieLocation[qie]][sh][r].Fill(slopes1[uid][1.0][r][qie][capID] / slopes1[uid][sh][r][qie][capID])
                    
                    shunt_factor_2[uid]["total"][sh][r].Fill(slopes2[uid][1.0][r][qie][capID] / slopes2[uid][sh][r][qie][capID])
                    shunt_factor_2[uid][qieLocation[qie]][sh][r].Fill(slopes2[uid][1.0][r][qie][capID] / slopes2[uid][sh][r][qie][capID])
                    shunt_factor_2["all"]["total"][sh][r].Fill(slopes2[uid][1.0][r][qie][capID] / slopes2[uid][sh][r][qie][capID])
                    shunt_factor_2["all"][qieLocation[qie]][sh][r].Fill(slopes2[uid][1.0][r][qie][capID] / slopes2[uid][sh][r][qie][capID])
               

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

grSF1_front = {"all":{} }
grSF1_back = {"all":{} }


for r in xrange(2):
    grSF1_front["all"][r] = TGraphErrors(len(foundShunts) - 1)
    grSF1_back["all"][r] = TGraphErrors(len(foundShunts) - 1)

    grSF1_front["all"][r].SetName("shunt_factors_front_range_%d" % r)
    grSF1_front["all"][r].SetTitle("Shunt Factors  Range %d  Front QIEs" % r)
    grSF1_front["all"][r].GetXaxis().SetTitle("Reference Shunt Factor")
    grSF1_front["all"][r].GetYaxis().SetTitle("Measured Shunt Factor")
    grSF1_back["all"][r].SetName("shunt_factors_back_range_%d" % r)
    grSF1_back["all"][r].SetTitle("Shunt Factors  Range %d  Back QIEs" % r)
    grSF1_back["all"][r].GetXaxis().SetTitle("Reference Shunt Factor")
    grSF1_back["all"][r].GetYaxis().SetTitle("Measured Shunt Factor")

    grSF1_front["all"][r].SetLineColor(kRed)
    grSF1_front["all"][r].SetMarkerColor(kRed)
    grSF1_back["all"][r].SetLineColor(kBlue)
    grSF1_back["all"][r].SetMarkerColor(kBlue)

for uid in uidList:
    grSF1_front[uid] = {}
    grSF1_back[uid] = {}
    for r in xrange(2):
        grSF1_front[uid][r] = TGraphErrors(len(foundShunts) - 1)
        grSF1_back[uid][r] = TGraphErrors(len(foundShunts) - 1)

        grSF1_front[uid][r].SetName("%s_shunt_factors_front_range_%d" % (uid,r))
        grSF1_front[uid][r].SetTitle("%s  Shunt Factors  Range %d  Front QIEs" % (uid,r))
        grSF1_back[uid][r].SetName("%s_shunt_factors_back_range_%d" % (uid,r))
        grSF1_back[uid][r].SetTitle("%s  Shunt Factors  Range %d  Back QIEs" % (uid,r))
        grSF1_front[uid][r].GetXaxis().SetTitle("Reference Shunt Factor")
        grSF1_front[uid][r].GetYaxis().SetTitle("Measured Shunt Factor")
        grSF1_back[uid][r].GetXaxis().SetTitle("Reference Shunt Factor")
        grSF1_back[uid][r].GetYaxis().SetTitle("Measured Shunt Factor")

        grSF1_front[uid][r].SetLineColor(kRed)
        grSF1_front[uid][r].SetMarkerColor(kRed)
        grSF1_back[uid][r].SetLineColor(kBlue)
        grSF1_back[uid][r].SetMarkerColor(kBlue)
        

for r in xrange(2):
    for sh in foundShunts:
        if sh < 1.3: continue
        np = grSF1_front["all"][r].GetN()
        grSF1_front["all"][r].SetPoint(np, sh, shunt_factor_1["all"]["front"][sh][r].GetMean())
        grSF1_front["all"][r].SetPointError(np, 0.01, shunt_factor_1["all"]["front"][sh][r].GetRMS())
        grSF1_back["all"][r].SetPoint(np, sh, shunt_factor_1["all"]["back"][sh][r].GetMean())
        grSF1_back["all"][r].SetPointError(np, 0.01, shunt_factor_1["all"]["back"][sh][r].GetRMS())

for uid in uidList:
    for sh in foundShunts:
        if sh < 1.3: continue
        for r in xrange(2):
            np = grSF1_front[uid][r].GetN()
            grSF1_front[uid][r].SetPoint(np, sh, shunt_factor_1[uid]["front"][sh][r].GetMean())
            grSF1_front[uid][r].SetPointError(np, 0.01, shunt_factor_1[uid]["front"][sh][r].GetRMS())
            grSF1_back[uid][r].SetPoint(np, sh, shunt_factor_1[uid]["back"][sh][r].GetMean())
            grSF1_back[uid][r].SetPointError(np, 0.01, shunt_factor_1[uid]["back"][sh][r].GetRMS())


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
        
        shunt_factor_1["all"]["total"][sh][r].Write()
        shunt_factor_1["all"]["front"][sh][r].Write()
        shunt_factor_1["all"]["back"][sh][r].Write()
        
        shunt_factor_2["all"]["total"][sh][r].Write()
        shunt_factor_2["all"]["front"][sh][r].Write()
        shunt_factor_2["all"]["back"][sh][r].Write()


for r in xrange(2):
    grSF1_front["all"][r].Write()
    grSF1_back["all"][r].Write()

for uid in uidList:
    d = outF.mkdir(uid)
    outF.cd(uid)
    for qie in xrange(1,17):
        d.mkdir("QIE_%d" % (qie))

    #d.mkdir("Run_%d_slope_vs_qie" % runNum1)
    #d.mkdir("Run_%d_slope_vs_qie" % runNum2)

for uid in uidList:
    for r in xrange(2):
        outF.cd(uid)
        grSF1_front[uid][r].Write()
        grSF1_back[uid][r].Write()

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
            
            shunt_factor_1[uid]["total"][sh][r].Write()
            shunt_factor_1[uid]["front"][sh][r].Write()
            shunt_factor_1[uid]["back"][sh][r].Write()
            
            shunt_factor_2[uid]["total"][sh][r].Write()
            shunt_factor_2[uid]["front"][sh][r].Write()
            shunt_factor_2[uid]["back"][sh][r].Write()
            
            for qie in xrange(1,17):
                outF.cd()
                outF.cd("%s/QIE_%d" % (uid,qie))
                h2D_slopes[uid][sh][r][qie].Write()
                h2D_offsets[uid][sh][r][qie].Write()

outF.Close()

sfDir = "%s/ShuntFactors1" % args.outDir

c = TCanvas("c","c",1000,800)
gStyle.SetOptStat(0)
print "Saving shunt factor plots"

for uid in uidList:
    os.system("mkdir -p %s/%s" % (sfDir,uid))
    for sh in foundShunts:
        if sh < 1.3: continue
        for r in xrange(4):
            if sh > 1 and r > 1: continue
            l = TLegend(0.75, 0.75, 0.9, 0.9)
            l.AddEntry(shunt_factor_1["all"]["front"][sh][r], "Front QIEs")
            l.AddEntry(shunt_factor_1["all"]["back"][sh][r], "Back QIEs")

            shunt_factor_1["all"]["front"][sh][r].SetTitle("Shunt Factors  Shunt %.1f Range %d" % (sh,r))
            shunt_factor_1["all"]["front"][sh][r].Draw("HIST")
            shunt_factor_1["all"]["back"][sh][r].Draw("HIST SAME")
            l.Draw("SAME")
            c.SaveAs("%s/shuntfactors_shunt_%s_range_%d.png" % (sfDir, str(sh).replace(".","_"),r))

            
            l = TLegend(0.75, 0.75, 0.9, 0.9)
            l.AddEntry(shunt_factor_1[uid]["front"][sh][r], "Front QIEs")
            l.AddEntry(shunt_factor_1[uid]["back"][sh][r], "Back QIEs")

            shunt_factor_1[uid]["front"][sh][r].SetTitle("%s  Shunt Factors  Shunt %.1f Range %d" % (uid,sh,r))
            shunt_factor_1[uid]["front"][sh][r].Draw("HIST")
            shunt_factor_1[uid]["back"][sh][r].Draw("HIST SAME")
            l.Draw("SAME")
            c.SaveAs("%s/%s/%s_shuntfactors_shunt_%s_range_%d.png" % (sfDir, uid, uid, str(sh).replace(".","_"),r))



for r in xrange(2):
    l = TLegend(0.75, 0.25, 0.9, 0.4)
    l.AddEntry(grSF1_front["all"][r], "Front QIEs")
    l.AddEntry(grSF1_back["all"][r], "Back QIEs")

    grSF1_front["all"][r].SetTitle("Shunt Factors  Range %d" % r)
    grSF1_front["all"][r].GetXaxis().SetTitle("Reference Shunt Factor")
    grSF1_front["all"][r].GetYaxis().SetTitle("Measured Shunt Factor")
    grSF1_front["all"][r].Draw("ALP")
    grSF1_back["all"][r].Draw("LP SAME")
    l.Draw("SAME")
    c.SaveAs("%s/shuntfactors_range_%d.png" % (sfDir,r))

    for uid in uidList:
        l = TLegend(0.75, 0.25, 0.9, 0.4)
        l.AddEntry(grSF1_front[uid][r], "Front QIEs")
        l.AddEntry(grSF1_back[uid][r], "Back QIEs")

        grSF1_front[uid][r].SetTitle("%s  Shunt Factors  Range %d" % (uid,r))
        grSF1_front[uid][r].GetXaxis().SetTitle("Reference Shunt Factor")
        grSF1_front[uid][r].GetYaxis().SetTitle("Measured Shunt Factor")
        grSF1_front[uid][r].Draw("ALP")
        grSF1_back[uid][r].Draw("LP SAME")
        l.Draw("SAME")
        c.SaveAs("%s/%s/shuntfactors_range_%d.png" % (sfDir,uid,r))




print "Done!\n"
