#!/usr/bin/env python
# Summary Plots For QIE Calibration
# Zach Shelton
#Located in Desktop/SummaryPlots
# Updated: 6/6/18 6:00PM CDT
# Imported Packages
import sqlite3
import pprint
import glob
import os
import sys
import argparse
import json
from MergeDatabases import MergeDatabases
from selectionCuts import *
from utils import Quiet


people = {'Brooks':'Brooks McMaster',
          'Bryan':'Bryan Caraway',
          'Caleb':'Caleb Smith',
          'Chris':'Chris Madrid',
          'Danny':'Danny "HF" Noonan',
          'Frank':'Frank Jensen',
          'Grace':'Grace Cummings',
          'Joe':'Joe Pastika',
          'Kamal':'Kamal Lamichhane',
          'Loriza':'Loriza Hasa',
          'Mark':'Mark Saunders',
          'Nadja':'Nadja Strobbe',
          'Nesta':'Nesta Lenhert',
          'Sezen':'Sezen Sekmen',
          'ZachE':'Zach Eckert',
          'Eckert':'Zach Eckert',
          'ZachS':'Zach Shelton',
          'Shelton':'Zach Shelton',
          }

backAdapter = [1,2,3,4,9,10,11,12]

hslopes = {}

hoffsets = {}

badShunts =[]

badOffset =[]

plotBoundaries_slope = [0.28, 0.36]

plotBoundaries_offset = [1, 16, 100, 800]

#FINDING ERROR PERCENTAGE
thshunt= .30
THRESHOLD = .15


from ROOT import *
#def SummaryPlot(options):
def SummaryPlot(runAll=False, dbnames=None, uid=None, total=False, date1=None, run1=None, hist2D=False, shFac=False, adapterTest=False,images=False, verbose=False, slVqie=False, tester1 = "Shelton",logoutput=False):
    # Get required arguments from options
    run = run1[0]
    date = date1[0]
    tester = tester1[0]
    gROOT.SetBatch(True)
    
    qieList = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

    #Canvases

    c = []
    c2 = []
    
    #Histogram Lists

    histoffset = []
    histshunt = []
    histslopes = []
    histSlopeNvSlope1 = []
    histShuntFactor = []
    histSlvQie = []

    #Total Histograms

    totalhist = []

    #Max - min Variables
    maximum = 0
    minimum = 0

    #Failure
    failure = False
    Result = True
    FailedCards = []
    FailedSlopes =[]
    FailedOffset = []
    #Set Axes Digits
    if not os.path.exists("data/%s/Run_%s/SummaryPlots"%(date, run)):
        os.makedirs("data/%s/Run_%s/SummaryPlots"%(date,run))
    if(runAll or not uid is None):
        files = glob.glob("data/%s/Run_%s/qieCalibrationParameters*.db"%(date,run))
    elif(len(dbnames) != 0):
        files = []
        for f in dbnames:
            files.append(glob.glob("data/%s/Run_%s/%s"%(date,run,f))[0])
    MergeDatabases(files, "data/%s/Run_%s/"%(date, run),"MergedDatabaseRun%s.db"%run)
    xyz1234 = sqlite3.connect("data/%s/Run_%s/MergedDatabaseRun%s.db"%(date, run,run))
    cursor = xyz1234.cursor()
    TGaxis.SetMaxDigits(3)
    #files = cursor.excute("Select distinct runDirectory from qieshuntparams").Fetchall()
    idlist = cursor.execute("Select distinct id from qieshuntparams").fetchall()
    # Get Ranges
    bins = cursor.execute("SELECT DISTINCT range FROM qieshuntparams").fetchall()

    # Get Shunts
    shunts = cursor.execute("SELECT DISTINCT shunt FROM qieshuntparams").fetchall()
    #if (runAll):
    for nameList in idlist:
        Result = True
        name = nameList[0]
	nameid = name.replace("u","")
	name = nameid.replace("'","")
	if not os.path.exists("data/%s/Run_%s/SummaryPlots/%s/ImagesOutput"%(date,run,name)):
            os.makedirs("data/%s/Run_%s/SummaryPlots/%s/ImagesOutput"%(date,run,name))	
	FailedCards = []
	FailedSlope =[]
	FailedOffset = []
	poorfits = []
        if not uid is None:
            if name not in uid:
                continue
        FailedCards = []
	if logoutput:
            originalSTDOUT = sys.stdout
	    originalSTDERR = sys.stderr 
            stdOutDump = open("data/%s/Run_%d/SummaryPlots/SummaryPlot.stdout"%(date,run), 'w+')
            sys.stdout = stdOutDump
	    sys.stderr = stdOutDump		
        #if not os.path.exists("data/%s/Run_%s/SummaryPlots/TotalPlots"%(date, run)):
            #os.makedirs("data/%s/Run_%s/SummaryPlots/TotalPlots"%(date, run))
            # Modify rootout change title of output ROOT file
	if(verbose):
	    print "Now analyzing card %s" %nameid
	rootout = TFile("data/%s/Run_%s/fitResults_%s.root" %(date, run, name), "update")
	rootout.cd("SummaryPlots")
	hline = TLine(0,0,0,0)
	hline.SetLineColor(2)
	lline = TLine(0,0,0,0)
	lline.SetLineColor(2)
	loline = TLine(0,0,0,0)
	loline.SetLineColor(2)
	holine = TLine(0,0,0,0)
	holine.SetLineColor(2)
        for ra in bins:
            r = ra[0]
            for shu in shunts:
                sh = shu[0]
                if (r == 2 or r == 3) and (sh != 1):
                    continue
                # Fetch the values of slope and offset for the corresponding shunt and range
                #values = cursor.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f and id = '%s';" % (r, sh,name)).fetchall()
                values = cursor.execute("select slope, range, offset, qie, capid, id, maxResidual, (SELECT slope from qieshuntparams where id=p.id and qie=p.qie and capID=p.capID and range=p.range and shunt=1) from qieshuntparams as p where range = %i and shunt = %.1f and id = '%s';"%(r,sh,name)).fetchall()

                # Fetch Max and minimum values for slope of shunt
                maxmin = cursor.execute("select max(slope),min(slope) from qieshuntparams where range=%i and shunt = %.1f and id = '%s';" % (r, sh,name)).fetchall()
                maximum, minimum = maxmin[0]
                maximums = max(plotBoundaries_slope[1]/sh, maximum+0.01)
                minimums = min(plotBoundaries_slope[0]/sh, minimum-0.01)
                if sh == 1:
                    maximum1 = maximums
                    minimum1 = minimums
                #Creates Canvases for each Shunt and Range(TH1D)
                c.append(TCanvas("Card_%s_Shunt_%.1f-Range_%i" % (name, sh, r), "histo"))
                c[-1].Divide(2,1)

                c[-1].cd(1)
                #Create Histograms for the shunt slopes
                histshunt.append(TH1D("SLOPE_Sh_%s_R_%i" %(str(sh).replace(".",""),r),"%s Shunt %.1f - Range %i" % (name, sh, r), 100, minimums, maximums))
                histshunt[-1].SetTitle("SLOPE SH: %.1f R: %d"%(sh,r))
                histshunt[-1].GetXaxis().SetTitle("Slope")
                histshunt[-1].GetYaxis().SetTitle("Frequency")
                gPad.SetLogy(1)

                #Create 2D histogram of slope of shunt N vs slope of shunt 1
                if(hist2D):
                    histSlopeNvSlope1.append(TH2D("Slope_Shunt_%s_vs_Shunt_1_R_%i"%(str(sh).replace(".",""),r),"%s Slope of Shunt %.1f vs Shunt 1 - Range %i"%(name,sh,r),100,minimum1,maximum1,100,minimums,maximums))
                    histSlopeNvSlope1[-1].GetXaxis().SetTitle("Shunt 1 Slope")
                    histSlopeNvSlope1[-1].GetYaxis().SetTitle("Shunt %.1f Slope"%sh)

                #Create 2D histogram of slope vs qie
                if(slVqie):
                    histSlvQie.append(TH2D("SlopeVsQIE_Shunt_%s_Range_%d"%(str(sh).replace(".",""),r),"%s Slope Vs QIE Shunt %.1f Range %d"%(name,sh,r),16,0.5,16.5,40,minimums,maximums))
                    histSlvQie[-1].GetXaxis().SetTitle("QIE")
                    histSlvQie[-1].GetYaxis().SetTitle("Slope")

                #Create histogram of shunt factor
                if(shFac):
                    histShuntFactor.append(TH1D("ShuntFactor_Sh_%s_R_%.i"%(str(sh).replace(".",""),r),"Shunt Factor Shunt %.1f Range %i"%(sh,r),100,sh-1,sh+1))
                    histShuntFactor[-1].GetXaxis().SetTitle("Shunt Factor")
                    histShuntFactor[-1].GetYaxis().SetTitle("Frequency")

                #Create Histograms for the Offsets
		maxmin = cursor.execute("select max(offset),min(offset) from qieshuntparams where range=%i and shunt = %.1f and id = '%s';" % (r, sh,name)).fetchall()
		maximumo,minimumo = maxmin[0]
                maximumo  = max(plotBoundaries_offset[r], maximum)
                minimumo  = min(-1*plotBoundaries_offset[r], minimum)
                test = []
                c[-1].cd(2)
                histoffset.append(TH1D("OFFSET_Sh_%s-R_%i" %(str(sh).replace(".",""),r),"%s Shunt %.1f - Range %d" %(name, sh, r), 41, minimumo, maximumo))
                histoffset[-1].SetTitle("OFFSET SH: %.1f R: %d"%(sh,r))
                histoffset[-1].GetXaxis().SetTitle("Offset")
                histoffset[-1].GetYaxis().SetTitle("Frequency")
                gPad.SetLogy(1)


                if adapterTest:
                    if sh not in hslopes.keys():
                        hslopes[sh] = {}
                    if r not in hslopes[sh].keys():
                        hslopes[sh][r] = {"total":{}, "front":{}, "back":{}}
                        for ty in ['total','front','back']:
                            hslopes[sh][r][ty] = TH1D("Slopes_shunt_%s_range_%d" % (str(sh).replace(".","_"), r), "Slopes  Shunt %.1f Range %d" % (sh,r), 100, minimums, maximums)
                            hslopes[sh][r][ty].SetDirectory(0)
                            hslopes[sh][r][ty].GetXaxis().SetTitle("Slope (LinADC / fC)")
                            hslopes[sh][r][ty].GetYaxis().SetTitle("QIE Channels")
                        hslopes[sh][r]['front'].SetTitle("Slopes  Front Adapter  Shunt %.1f Range %d" % (sh,r))
                        hslopes[sh][r]['back'].SetTitle("Slopes  Back Adapter  Shunt %.1f Range %d" % (sh,r))
                    if sh not in hoffsets.keys():
                        hoffsets[sh] = {}
                    if r not in hoffsets[sh].keys():
                        hoffsets[sh][r] = {"total":{}, "front":{}, "back":{}}
                        for ty in ['total','front','back']:
                            hoffsets[sh][r][ty] = TH1D("Offsets_shunt_%s_range_%d" % (str(sh).replace(".","_"), r), "Offsets  Shunt %.1f Range %d" % (sh,r), 100, minimumo, maximumo)
                            hoffsets[sh][r][ty].SetDirectory(0)
                            hoffsets[sh][r][ty].GetXaxis().SetTitle("Offset (LinADC)")
                            hoffsets[sh][r][ty].GetYaxis().SetTitle("QIE Channels")
                        hoffsets[sh][r]['front'].SetTitle("Slopes  Front Adapter  Shunt %.1f Range %d" % (sh,r))
                        hoffsets[sh][r]['back'].SetTitle("Slopes  Back Adapter  Shunt %.1f Range %d" % (sh,r))
		
                # Fills the histograms with the values fetched above
                for val in values:
                    #slope, offset = val
                    slope, rang, offset,qie,capid , id,maxr, slSh1= val
                    if slopeFailH(sh,rang,id,slope):
                        FailedSlope.append((sh,rang,qie,capid))
			Result = False
			if(verbose):                            
			    print "Slope in CAPID %i in QIE %i in Shunt %.1f and Range %i"%(capid,qie,sh,r)
                    elif offsetFail(rang,offset,id):
                        FailedOffset.append((sh,rang,qie,capid))
			Result = False
			if(verbose):                            
			    print "Offset in CAPID %i in QIE %i in Shunt %.1f and Range %i"%(capid,qie,sh,r)
		    if poorfit(maxr,rang):
			Result = False
			poorfits.append((sh,rang,qie,capid))
			if (verbose):
			    print "Poor fitting results in CAPID %i in QIE %i in Shunt %.1f and Range %i"%(capid,qie,sh,r)
                    c[-1].cd(1)
                    histshunt[-1].Fill(slope)
		    histshunt[-1].Draw()
		    hline.DrawLine(failureconds[sh][1],0,failureconds[sh][1],histshunt[-1].GetMaximum()+1)
	            hline.Draw("same")
		    lline.DrawLine(failureconds[sh][0],0,failureconds[sh][0],histshunt[-1].GetMaximum()+1)
		    lline.Draw("same")
                    c[-1].cd(2)
                    histoffset[-1].Fill(offset)
                    histoffset[-1].Draw()
                    if adapterTest:
                        hslopes[sh][r]['total'].Fill(slope)
                        hoffsets[sh][r]['total'].Fill(offset)
                        if qie in backAdapter:
                            hslopes[sh][r]['back'].Fill(slope)
                            hoffsets[sh][r]['back'].Fill(offset)
                        else:
                            hslopes[sh][r]['front'].Fill(slope)
                            hoffsets[sh][r]['front'].Fill(offset)
                    #c[-1].cd(3)
                    if(slVqie):
                        histSlvQie[-1].Fill(qie,slope)
                    if(hist2D):
                        histSlopeNvSlope1[-1].Fill(slSh1,slope)
                    if(shFac):
                        try:
                            histShuntFactor[-1].Fill(slSh1/slope)
                        except ZeroDivisionError:
                            print "Divide by Zero Error: %s Shunt %.1f Range %d"%(name,sh,r)
		if r == 0:
		    holine.DrawLine(-.5,0,-.5,histoffset[-1].GetMaximum()+1)
	       	    holine.Draw("same")	
		else:
		    holine.DrawLine(failcondo[r][0],0,failcondo[r][0],histoffset[-1].GetMaximum()+1)
	       	    holine.Draw("same")
	            loline.DrawLine(-failcondo[r][0],0,-failcondo[r][0],histoffset[-1].GetMaximum()+1)
	            loline.Draw("same")
	        histshunt[-1].Write()
	        histoffset[-1].Write()
	        c[-1].Update()
                #c[-1].SaveAs("data/%s/Run_%s/SummaryPlots/ImagesOutput/CARD_%s_SHUNT_%s_RANGE_%i.png"%(date, run, name, str(sh).replace(".",""), r))
                if(images):
                    #c[-1].SaveAs("data/%s/Run_%s/SummaryPlots/%s/ImagesOutput/%s_SHUNT_%s_RANGE_%i.png"%(date, run, name,name, str(sh).replace(".",""), r))
		    Quiet(c[-1].SaveAs)("data/%s/Run_%s/SummaryPlots/%s/ImagesOutput/%s_SHUNT_%s_RANGE_%i.png"%(date, run, name,name, str(sh).replace(".",""), r))
                if(hist2D):
                    histSlopeNvSlope1[-1].Write()
                if(shFac):
                    histShuntFactor[-1].Write()
                if(slVqie):
                    histSlvQie[-1].Write()
                if(verbose):
                    print "Card %s Shunt %.1f Range %d Finished"%(name,sh,r)
	FailedCards.append({name:{'Offset':FailedOffset,'Slope':FailedSlope,'poor fit': poorfit}})
	cardplaceholder = {'Result':Result,'date':date, 'run':run, 'Tester':people[tester], 'Comments':{'Offset':FailedOffset,'Slope':FailedSlope, 'Poor fit':poorfits}}
	file1 = open("data/%s/Run_%s/SummaryPlots/%s/%s.json"%(date,run,name,name),"w+")
	json.dump(cardplaceholder, file1)
	    
        if (adapterTest):
            rundir = "data/%s/Run_%s/SummaryPlots" % (date, run)
            outdir = "adapterTests"
            os.system("mkdir -p %s/%s" % (rundir, outdir))
            c.append(TCanvas("c","c",1600,1200))
            ranges = xrange(4)
            gStyle.SetOptStat(0)
        if adapterTest:
            for ra in bins:
                r=ra[0]
                for shu in shunts:
                    sh = shu[0]
                    if (r == 2 or r == 3) and (sh != 1):
                        continue
                    l = TLegend(0.75, 0.75, 0.9, 0.9)
                    print hslopes
                    print sh, r
                    l.AddEntry(hslopes[sh][r]['front'], "Front adapter")
                    l.AddEntry(hslopes[sh][r]['back'], "Back adapter")
                    hslopes[sh][r]['front'].SetLineColor(2)
                    hslopes[sh][r]['front'].SetLineWidth(2)
                    hslopes[sh][r]['back'].SetLineColor(4)
                    hslopes[sh][r]['back'].SetLineWidth(2)
    
                    hslopes[sh][r]['back'].SetTitle("Slopes  Shunt %.1f Range %d" % (sh,r))
                    hslopes[sh][r]['back'].Draw("HIST")
                    hslopes[sh][r]['front'].Draw("HIST SAME")
                    l.Draw("SAME")
                    if(images):
                        (c[-1].SaveAs)("%s/%s/slopes_shunt_%s_range_%d.png" % (rundir,outdir,str(sh).replace(".","_"),r))
    
                    lo = TLegend(0.75, 0.75, 0.9, 0.9)
                    lo.AddEntry(hslopes[sh][r]['front'], "Front adapter")
                    lo.AddEntry(hslopes[sh][r]['back'], "Back adapter")
    
                    hoffsets[sh][r]['front'].SetLineColor(2)
                    hoffsets[sh][r]['front'].SetLineWidth(2)
                    hoffsets[sh][r]['back'].SetLineColor(4)
                    hoffsets[sh][r]['back'].SetLineWidth(2)
    
                    hoffsets[sh][r]['back'].SetTitle("Offsets  Shunt %.1f Range %d" %(sh,r))
                    hoffsets[sh][r]['back'].Draw("HIST")
                    hoffsets[sh][r]['front'].Draw("HIST SAME")
                    lo.Draw("SAME")
                    if(images):
                        Quiet(c[-1].SaveAs)("%s/%s/offsets_shunt_%s_range_%d.png" % (rundir,outdir,str(sh).replace(".","_"),r))
    if (total):
        name = nameList[0]
        if not os.path.exists("data/%s/Run_%s/SummaryPlots"%(date, run)):
            os.makedirs("data/%s/Run_%s/SummaryPlots"%(date,run))
        if not os.path.exists("data/%s/Run_%s/SummaryPlots/TotalOutput"%(date, run)):
            os.makedirs("data/%s/Run_%s/SummaryPlots/TotalOutput"%(date,run))
            # Modify rootout change title of output ROOT file
        rootout = TFile("data/%s/Run_%s/SummaryPlots/summary_plot_total.root" %(date, run), "recreate")
        for ra in bins:
            r =ra[0]
            for shu in shunts:
                sh = shu[0]
                if (r == 2 or r == 3) and (sh != 1):
                    continue
                # Fetch the values of slope and offset for the corresponding shunt and range
                # values = cursor.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f ;" % (r, sh)).fetchall()
                values = cursor.execute("select slope, range, offset, qie, capid, id, maxResidual,(SELECT slope from qieshuntparams where id=p.id and qie=p.qie and capID=p.capID and range=p.range and shunt=1) from qieshuntparams as p where range = %i and shunt = %.1f;"%(r,sh)).fetchall()
                # Fetch Max and minimum values for slope of shunt
                maxmin = cursor.execute("select max(slope),min(slope) from qieshuntparams where range=%i and shunt = %.1f;" % (r,sh)).fetchall()
                maximum, minimum = maxmin[0]
                maximums = max(plotBoundaries_slope[1]/sh, maximum+0.01)
                minimums = min(plotBoundaries_slope[0]/sh, minimum-0.01)
                if sh == 1:
                    maximum1 = maximums
                    minimum1 = minimums
                #Creates Canvases for each Shunt and Range(TH1D)
                c.append(TCanvas("Shunt %.1f  -  Range %i" % (sh, r), "histo"))
                c[-1].Divide(2,1)

                #Create Histograms for the shunt slopes
                histshunt.append(TH1D("SLOPE_Sh:_%.1f_RANGE_r:_%d" %(sh,r),"SLOPE Sh: %.1f RANGE r: %d" %(sh,r), 100, minimums, maximums))
                #histshunt[-1].SetTitle("SLOPE SH: %.1f "%(sh))
                histshunt[-1].GetXaxis().SetTitle("Slope")
                histshunt[-1].GetYaxis().SetTitle("Frequency")
                gPad.SetLogy(1)

                #Create 2D histogram of slope of shunt N vs slope of shunt 1
                if(hist2D):
                    histSlopeNvSlope1.append(TH2D("Slope_Shunt_%s_vs_Shunt_1_R_%i"%(str(sh).replace(".",""),r),"Slope of Shunt %.1f vs Shunt 1 - Range %i"%(sh,r),100,minimum1,maximum1,100,minimums,maximums))
                    histSlopeNvSlope1[-1].GetXaxis().SetTitle("Shunt 1 Slope")
                    histSlopeNvSlope1[-1].GetYaxis().SetTitle("Shunt %.1f Slope"%sh)

                #Create histogram of shunt factor
                if(shFac):
                    histShuntFactor.append(TH1D("ShuntFactor_Sh_%s_R_%.i"%(str(sh).replace(".",""),r),"Shunt Factor Shunt %.1f Range %i"%(sh,r),100,sh-1,sh+1))
                    histShuntFactor[-1].GetXaxis().SetTitle("Shunt Factor")
                    histShuntFactor[-1].GetYaxis().SetTitle("Frequency")
                #Create Histograms for the Offsets
                maxmin = cursor.execute("select max(offset),min(offset) from qieshuntparams where range=%i and shunt = %.1f;" % (r, sh)).fetchall()
                maximum, minimum = maxmin[0]
                maximumo  = max(plotBoundaries_offset[r], maximum)
                minimumo  = min(-1*plotBoundaries_offset[r], minimum)

                c[-1].cd(2)
                histoffset.append(TH1D("OFFSET Sh: %.1f - R: %i" %(sh, r),"Shunt %.1f - Range %d" %(sh, r), 40, minimumo, maximumo))
                histoffset[-1].SetTitle("OFFSET SH: %.1f R: %d"%(sh,r))
                histoffset[-1].GetXaxis().SetTitle("Offset")
                histoffset[-1].GetYaxis().SetTitle("Frequency")
                gPad.SetLogy(1)
                # Fills the histograms with the values fetched above
                for val in values:
                    #slope, offset = val
                    try:
                        slope,rang, offset, qie, capid, id ,maxr,slSh1 = val
                    except:
                        print val
                    histshunt[-1].Fill(slope)
                    histshunt[-1].Draw()
                    c[-1].cd(2)
                    histoffset[-1].Fill(offset)
                    histoffset[-1].Draw()
                    if(hist2D):
                        histSlopeNvSlope1[-1].Fill(slSh1,slope)
                    if(shFac):
                        try:
                            histShuntFactor[-1].Fill(slSh1/slope)
                        except ZeroDivisionError:
                            pass
                # Write the histograms to the file, saving them for later
                # histshunt[-1].Draw()
                # histoffset[-1].Draw()
                # c2[-1].Write()
                c[-1].Update()
                #c[-1].SaveAs("data/%s/Run_%s/SummaryPlots/ImagesOutput/CARD_%s_SHUNT_%s_RANGE_%i.png"%(date, run, name, str(sh).replace(".",""), r))
                if(images):
                    c[-1].Print("data/%s/Run_%s/SummaryPlots/TotalOutput/Total_SHUNT_%s_RANGE_%i.png"%(date, run, str(sh).replace(".",""), r))
                c[-1].Write()
                if(hist2D):
                    histSlopeNvSlope1[-1].Write()
                if(shFac):
                    histShuntFactor[-1].Write()
                if(verbose):
                    print "Total Plots Shunt %.1f Range %d Finished"%(sh,r)
    if len(FailedCards) >=1:
        outputText = open("data/%s/Run_%s/SummaryPlots/Failed_Shunts_and_Ranges.txt"%(date,run),"w+")
        pprint.pprint(FailedCards, outputText)
        outputText.close()
	
    rootout.Close()
    if logoutput:
        sys.stdout = originalSTDOUT
	sys.stderr = originalSTDERR

def slopeFailTh(sh, r, name,slope,thshunt = .3,pct = .1):
    maxt=(thshunt/sh)+(thshunt/sh)*THRESHOLD
    mint=(thshunt/sh)-(thshunt/sh)*THRESHOLD
    failure = False
    if sh == 1:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 1.5:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 2:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 3:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 4:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 5:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 6:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 7:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 8:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 9:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 10:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 11:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 11.5:
        if (mint > slope or slope > maxt):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    return failure
# THIS PASS FAIL USES HARDCODED SLOPE VALUES TO DETERMINE ERRORS
def slopeFailH(sh, r, name,slope,thshunt = .3,pct = .1):
    #maxt=(thshunt/sh)+(thshunt/sh)*THRESHOLD
    #mint=(thshunt/sh)-(thshunt/sh)*THRESHOLD
    failure = False
    if sh == 1:
        if (.28 > slope or slope > .331):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 1.5:
        if (.19 > slope or slope > .225):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 2:
        if (.147 > slope or slope > .168):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 3:
        if (.099 > slope or slope > .1135):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 4:
        if (.075 > slope or slope > .0865):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 5:
        if (.0595 > slope or slope > .069):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 6:
        if (.05 > slope or slope > .0575):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 7:
        if (.0425 > slope or slope > .495):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 8:
        if (.037 > slope or slope > .044):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 9:
        if (.033 > slope or slope > .039):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 10:
        if (.03 > slope or slope > .0355):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 11:
        if (.027 > slope or slope > .032):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    if sh == 11.5:
        if (.025 > slope or slope > .03):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure = True
    return failure

def offsetFail(r,offset,name):
    failure= False
    if r == 0:
        if (offset > 0 or offset < -1):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure=True
    if r == 1:
        if (offset > 12 or offset < -12):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure=True
    if r == 2:
        if (offset > 80 or offset < -80):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure=True
    if r == 3:
        if (offset > 800 or offset < -800):
            # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
            failure=True
    return failure
def poorfit(maxr, r):
    failure = False
    if r == 0:
        if (maxr > 4.5):
            failure=True
    if r == 1:
        if (maxr > 35):
            failure=True
    if r == 2:
        if (maxr > 300):
            failure=True
    if r == 3:
        if (maxr > 2000):
            failure=True
    return failure
    
###################################################################################
uid = []
dbnames = []
arg = ''
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This produces Summary Plots for runs')
    parser.add_argument('-a','--all', action="store_true", dest='all', default=False, help = "Creates plots for all files and a combined database")
    parser.add_argument('-f','--files', action="append", dest = 'dbnames', help  = "Creates Summary Plots for a  file(s) list with -f [FILENAME] -f [FILENAME]")
    parser.add_argument('-u','--uniqueID', action="append", dest = 'uid', help  = "Creates Summary Plots for a  file(s) based on Unique IDs list with -u [UniqueID] -u [UniqueID] -u [UniqueID] (format uniqueID as '0xXXXXXXXX_0xXXXXXXXX')")
    parser.add_argument('-t','--total', action="store_true", dest="total", default = False, help = "Creates total histograms for each shunt WARNING Adapter Test Will not be done with this arg(WARNING: TOTAL OUT OF DATE, MAY BE NON_FUNCTIONING")
    parser.add_argument('-d','--date', required=True, action="append", dest="date", help = "Enter date in format XX-XX-XXXX(Required)")
    parser.add_argument('-r','--run', required=True, action="append", dest="run", type = int,help = "Enter the number run(Required)")
    parser.add_argument('-2','--hist2D',action="store_true",dest="hist2D",default=False,help="Creates 2D histogram of slope of shunt N vs. slope of shunt 1")
    parser.add_argument('-s','--shuntFactor',action="store_true",dest="shFac",default=False,help="Creates histogram of shunt factors")
    parser.add_argument('--noImages',action="store_false",dest="images",default=True,help="Do not save images")
    parser.add_argument('--verbose',action="store_true",dest="verbose",default=False,help="Print progress messages")
    parser.add_argument('--slVqie',action="store_true",dest="slVqie",default=False,help="Create Plot of Slope vs QIE")
    parser.add_argument('--log',action="store_true",dest="log",default=False,help="Dump to .std file")
    parser.add_argument('--tester',required=True,action="append",dest="tester",type=str,help="Define tester")
    options = parser.parse_args()

#    SummaryPlot(options)
    SummaryPlot(runAll = options.all, dbnames = options.dbnames, uid = options.uid, total = options.total, date1 = options.date, run1 = options.run, hist2D = options.hist2D, shFac = options.shFac, images = options.images, verbose = options.verbose, slVqie = options.slVqie,logoutput = options.log,tester1 =options.tester)
