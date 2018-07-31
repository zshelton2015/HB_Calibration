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
          'Ian':'Ian McAlister',
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

plotBoundaries_slope = [0.27, 0.36]

plotBoundaries_offset = [1, 16, 100, 900]

#FINDING ERROR PERCENTAGE
thshunt= .30
THRESHOLD = .15


from ROOT import *
#def SummaryPlot(options):
def SummaryPlot(runAll=False, dbnames=None, uid=None, total=False, idir = "", hist2D=False, shFac=False, adapterTest=False,images=False, verbose=False, slVqie=False, tester1 = "Shelton",logoutput=False):
    # Get required arguments from options
    tester = tester1
    indir = idir[0]
    date = indir[5:15]
    run = indir[-1]

    if indir == None:
        print "invalid indirectory"
        exit
    if indir[-1] != "/":
        indir+="/"
    run = indir[20:-2]
    if type(tester) == type([]):
        tester = tester[0]
        if tester in people:
            tester = people[tester]
    elif type(tester) == type(""):
        if tester in people:
            tester = people[tester]
        elif tester in people.values():
            tester = tester
        else:
            print "Tester not in list of testers"
    else:
        print "Tester type error"

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
    FailedRange = []
    #Grab File Names
    if not os.path.exists("%sSummaryPlots"%(indir)):
        os.makedirs("%sSummaryPlots"%(indir))
    if(runAll or total or not uid is None):
        files = glob.glob("%sqieCalibrationParameters*.db"%(indir))
    elif(len(dbnames) != 0):
        files = []
        for f in dbnames:
            files.append(glob.glob("%s/%s"%(indir,f))[0])
    print files
    MergeDatabases(files, indir,"MergedDatabaseRun%s.db"%run)
    xyz1234 = sqlite3.connect("%sMergedDatabaseRun%s.db"%(indir,run))
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
        if not os.path.exists("%sSummaryPlots/%s/ImagesOutput"%(indir,name)):
             os.makedirs("%sSummaryPlots/%s/ImagesOutput"%(indir,name))
        FailedCards = []
        FailedSlope =[]
        FailedOffset = []
        poorfits = []
        FailedRange = []
        OffsetMean = []
        if not uid is None:
            if name not in uid:
                 continue
            FailedCards = []
        if logoutput:
                originalSTDOUT = sys.stdout
                stdOutDump = open("%sSummaryPlots/SummaryPlot.stdout"%(indir), 'w+')
                sys.stdout = stdOutDump
            #if not os.path.exists("data/%s/Run_%s/SummaryPlots/TotalPlots"%(date, run)):
                #os.makedirs("data/%s/Run_%s/SummaryPlots/TotalPlots"%(date, run))
                # Modify rootout change title of output ROOT file

        rootout = TFile("%sfitResults_%s.root" %(indir, name), "update")
        rootout.cd("SummaryPlots")
        if(verbose):
            print "Now analyzing card %s" %nameid
        if(runAll):
            for ra in bins:
                r = ra[0]
                for shu in shunts:
                    sh = shu[0]
                    if (r == 2 or r == 3) and (sh != 1):
                        continue
                    # Fetch the values of slope and offset for the corresponding shunt and range
                    #values = cursor.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f and id = '%s';" % (r, sh,name)).fetchall()
                    values = cursor.execute("select slope, range, offset, qie, capid, maxX,minX, id, maxResidual, (SELECT slope from qieshuntparams where id=p.id and qie=p.qie and capID=p.capID and range=p.range and shunt=1) from qieshuntparams as p where range = %i and shunt = %.1f and id = '%s';"%(r,sh,name)).fetchall()

                # Fetch Max and minimum values for slope of shunt
                    maxmin = cursor.execute("select max(slope),min(slope) from qieshuntparams where range=%i and shunt = %.1f and id = '%s';" % (r, sh,name)).fetchall()
                    maximum, minimum = maxmin[0]
                    maximums = max(plotBoundaries_slope[1]/sh, maximum+0.01)
                    minimums = min(plotBoundaries_slope[0]/sh, minimum-0.01)
                    if sh == 1:
                        maximum1 = maximums
                        minimum1 = minimums
                    #Creates Canvases for each Shunt and Range(TH1D)
                    c.append(TCanvas("Card_%s_Shunt_%.1f_Range_%i" % (name, sh, r), "histo"))
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
                    maximum,minimum = maxmin[0]
                    maximumo  = max(plotBoundaries_offset[r], maximum)
                    minimumo  = min(-1*plotBoundaries_offset[r], minimum)
                    test = []
                    c[-1].cd(2)
                    histoffset.append(TH1D("OFFSET_Sh_%s_R_%i" %(str(sh).replace(".",""),r),"%s Shunt %.1f - Range %d" %(name, sh, r), 41, minimumo, maximumo))
                    histoffset[-1].SetTitle("OFFSET SH: %.1f R: %d"%(sh,r))
                    histoffset[-1].GetXaxis().SetTitle("Offset")
                    histoffset[-1].GetYaxis().SetTitle("Frequency")
                    gPad.SetLogy(1)
                    hline = TLine(0,0,0,0)
                    hline.SetLineColor(2)
                    lline = TLine(0,0,0,0)
                    lline.SetLineColor(2)
                    loline = TLine(0,0,0,0)
                    loline.SetLineColor(2)
                    holine = TLine(0,0,0,0)
                    holine.SetLineColor(2)


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
                        slope, rang, offset,qie,capid ,minX,maxX, id,maxr, slSh1= val
                        if XrangeFail(sh,rang,minX,maxX):
                            FailedRange.append((sh,rang,qie,capid))
                            Result = False
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
                    if(images):
                        Quiet(c[-1].SaveAs)("%sSummaryPlots/%s/ImagesOutput/%s_SHUNT_%s_RANGE_%i.png"%(indir, name,name, str(sh).replace(".",""), r))
                    if(hist2D):
                        histSlopeNvSlope1[-1].Write()
                    if(shFac):
                        histShuntFactor[-1].Write()
                    if(slVqie):
                        histSlvQie[-1].Write()
                    if(verbose):
                        print "Card %s Shunt %.1f Range %d Finished"%(name,sh,r)
        for ran in bins:
            for sh in shunts:
                r =ran[0]
                s = sh[0]
                if (r>1) and s!=1:
                    continue
                offset1 = cursor.execute("Select avg(offset) from qieshuntparams where shunt =%.1f and  id ='%s' and  range = %d"%(s,name,r)).fetchall()
                offset = offset1[0]
                if offset[0] < rangemean[r][0] or offset[0] > rangemean[r][1]:
                    OffsetMean.append((s,r))
                    Result = False
                    if(verbose):
                        print "qie and capid is indicative of a failure in the mean of the Offset"
        rootout.Close()
        FailedCards.append({name:{'Offset':FailedOffset,'Slope':FailedSlope,'poor fit': poorfit,'Bad Mean Offset':OffsetMean,'Range Failures':FailedRange}})
        cardplaceholder = {'Result':Result,'date':date, 'run':run, 'Tester':tester, 'Comments':{'Offset':FailedOffset,'Slope':FailedSlope, 'Poor fit':poorfits,'Bad Mean Offset':OffsetMean,'Range Failures':FailedRange}}
        file1 = open("%sSummaryPlots/%s/%s.json"%(indir,name,name),"w+")
        json.dump(cardplaceholder, file1)
    if (adapterTest):
        rundir = "%sSummaryPlots" %indir
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
        hline = TLine(0,0,0,0)
        hline.SetLineColor(2)
        lline = TLine(0,0,0,0)
        lline.SetLineColor(2)
        loline = TLine(0,0,0,0)
        loline.SetLineColor(2)
        holine = TLine(0,0,0,0)
        holine.SetLineColor(2)
        if not os.path.exists("%sSummaryPlots"%indir):
            os.makedirs("%sSummaryPlots"%indir)
        if not os.path.exists("%sSummaryPlots/TotalOutput"%indir):
            os.makedirs("%sSummaryPlots/TotalOutput"%indir)
            # Modify rootout change title of output ROOT file
        rootout = TFile("%sSummaryPlots/summary_plot_total.root" %indir, "recreate")
        for ra in bins:
            r =ra[0]
            for shu in shunts:
                sh = shu[0]
                if (r == 2 or r == 3) and (sh != 1):
                    continue
                # Fetch the values of slope and offset for the corresponding shunt and range
                # values = cursor.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f ;" % (r, sh)).fetchall()
                values = cursor.execute("select slope, offset from qieshuntparams as p where range = %i and shunt = %.1f;"%(r,sh)).fetchall()
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
                c[-1].cd(1)
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
                    try:
                        slope, offset = val
                    except:
                        print val
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
                    if r == 0:
                        holine.DrawLine(-.49,0,-.49,histoffset[-1].GetMaximum()+1)
                        holine.Draw("same")
                        loline.DrawLine(-.51,0,-.51,histoffset[-1].GetMaximum()+1)
                        loline.Draw("same")
                    else:
                        holine.DrawLine(failcondo[r][0],0,failcondo[r][0],histoffset[-1].GetMaximum()+1)
                        holine.Draw("same")
                        loline.DrawLine(-failcondo[r][0],0,-failcondo[r][0],histoffset[-1].GetMaximum()+1)
                        loline.Draw("same")
                    histshunt[-1].Write()
                    histoffset[-1].Write()
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
            outputText = open("%sSummaryPlots/Failed_Shunts_and_Ranges.txt"%indir,"w+")
            pprint.pprint(FailedCards, outputText)
            outputText.close()

        rootout.Close()
        if logoutput:
            sys.stdout = originalSTDOUT

#   sys.stderr = originalSTDERR


# THIS PASS FAIL USES HARDCODED SLOPE VALUES TO DETERMINE ERRORS
def slopeFailH(sh, r, name,slope,thshunt = .3,pct = .1):
    from selectionCuts import *
    failure = False
    if slope<failureconds[sh][0] or slope > failureconds[sh][1]:
        failure = True
    return failure
def XrangeFail(sh, r,xmin,xmax):
    from selectionCuts import *
    failure = False
    if xmin<chargeRange[r][sh]['min'] or xmax > chargeRange[r][sh]['max']:
        failure = True
    return failure


def offsetFail(r,offset,name):
    from selectionCuts import *
    failure= False
    if r==0:
        if (offset > -.45 or offset < -.55):
            failure = True
    elif (offset > failcondo[r][0] or offset < -1*(failcondo[r][0])):
        # print "Slope Value in Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
        failure=True
    return failure
def poorfit(maxra, r):
    from selectionCuts import *
    maxr = abs(maxra)
    failure = False
    if (maxr > maxResiduals[r]):
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
    parser.add_argument('-2','--hist2D',action="store_true",dest="hist2D",default=False,help="Creates 2D histogram of slope of shunt N vs. slope of shunt 1")
    parser.add_argument('-s','--shuntFactor',action="store_true",dest="shFac",default=False,help="Creates histogram of shunt factors")
    parser.add_argument('--noImages',action="store_false",dest="images",default=True,help="Do not save images")
    parser.add_argument('--verbose',action="store_true",dest="verbose",default=False,help="Print progress messages")
    parser.add_argument('--slVqie',action="store_true",dest="slVqie",default=False,help="Create Plot of Slope vs QIE")
    parser.add_argument('--log',action="store_true",dest="log",default=False,help="Dump to .std file")
    parser.add_argument('--tester',required=True,action="append",dest="tester",type=str,help="Define tester")
    parser.add_argument('-d,''--dir',action="append",dest = "inDir", type = str,help= "enter directory of run")
    options = parser.parse_args()
    SummaryPlot(runAll = options.all, dbnames = options.dbnames, uid = options.uid, total = options.total, idir = options.inDir, hist2D = options.hist2D, shFac = options.shFac, images = options.images, verbose = options.verbose, slVqie = options.slVqie,logoutput = options.log,tester1 =options.tester)
