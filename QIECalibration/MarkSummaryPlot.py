#!/usr/bin/env python
# Summary Plots For QIE Calibration
# Zach Shelton
##Located in Desktop/SummaryPlots
# Updated: 6/6/18 6:00PM CDT
# Imported Packages
import sqlite3
from ROOT import *
import pprint
import glob
import os
import sys
gROOT.SetBatch(True)
import pickle

plotBoundaries_slope = [0.28,0.33]

#plotBoundaries_offset = [1,16,100,800]
plotBoundaries_offset = [1,25,100,800]


backAdapter = [1,2,3,4,9,10,11,12]



shunts = [1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11.5]
hslopes = {}
hoffsets = {}


def SummaryPlot(database, arg, date, run):
    bins = [0, 1, 2, 3]
    counter = 0
    countbin = 0
    fcard = []
    frange = []
    fshunt = []
    c = []
    c2 = []
    histoffset = []
    databases = []
    histshunt = []
    totalhist = []
    maximum = 0
    minimum = 0
    failure = False
    FailedCards = {'Card': fcard, 'Ranges': frange, 'Shunts': fshunt}
    databases = glob.glob("data/%s/Run_%s/qieCalibrationParameters*.db"%(date, run))
    if not os.path.exists("data/%s/Run_%s/SummaryPlots"%(date,run)):
        os.makedirs("data/%s/Run_%s/SummaryPlots"%(date,run))
    if not os.path.exists("data/%s/Run_%s/SummaryPlots/ImagesOutput"%(date,run)):
        os.makedirs("data/%s/Run_%s/SummaryPlots/ImagesOutput"%(date,run))
    if not os.path.exists("data/%s/Run_%s/SummaryPlots/Log"%(date,run)):
        os.makedirs("data/%s/Run_%s/SummaryPlots/Log"%(date,run))
    if not os.path.exists("data/%s/Run_%s/SummaryPlots/TotalPlots"%(date,run)):
        os.makedirs("data/%s/Run_%s/SummaryPlots/TotalPlots"%(date,run))
    TGaxis.SetMaxDigits(3)
    if arg == 't':
        output = TFile("data/%s/Run_%s/SummaryPlots/Summary_Of_Run.root"%(date,run),"recreate")
        for j in range(0,len(shunts)):
            #totalshunts.append(TCanvas("Total Shunts for %.1f"%shunts[j],"histo"))
            c.append(TCanvas("SLOPE AT SHUNT - %.1f" %shunts[j], "histo"))
            totalhist.append(TH1D("Total Shunts for %.1f"%shunts[j],"Total Shunts for %.1f"%shunts[j],200, 0 , .5))
        for data in databases:
            xyz1234 = sqlite3.connect(data)
            cursor = xyz1234.cursor()
            name = data[data.find("_0x"):data.find(".")]
            countbin= 0
            for r in bins:  # Ranges
                counter= 0
                for sh in shunts:
                    # Fetch the values of slope and offset for the corresponding shunt and range
                    values = cursor.execute("select slope,offset from qieshuntparams where range=%i and shunt=%.1f;" % (r, sh)).fetchall()
                    gPad.SetLogy(1)
                    for val in values:
                        slope, offset = val
                        totalhist[counter].Fill(slope)
                        totalhist[counter].Draw()
                    totalhist[counter].Write()
                    maxmin = cursor.execute("select max(slope),min(slope) from qieshuntparams where range=%i and shunt = %.1f;" % (r, sh)).fetchall()
                    maximum, minimum = maxmin[0]
                    if sh == 1:
                        if 0.283 > minimum or maximum > 0.326:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 1.5:
                        if 0.185 > minimum or maximum > 0.22:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 2:
                        if 0.143 > minimum or maximum > 0.168:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 3:
                        if 0.095 > minimum or maximum > 0.115:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 4:
                        if 0.072 > minimum or maximum > 0.085:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 5:
                        if 0.0575 > minimum or maximum > 0.068:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 6:
                        if 0.048 > minimum or maximum > 0.064:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 7:
                        if 0.041 > minimum or maximum > 0.05:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 8:
                        if 0.036 > minimum or maximum > 0.044:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 9:
                        if 0.032 > minimum or maximum > 0.039:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 10:
                        if 0.029 > minimum or maximum > 0.035:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 11:
                        if 0.026 > minimum or maximum > 0.032:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if sh == 11.5:
                        if 0.025 > minimum or maximum > 0.031:
                            print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                            failure = True
                    if failure:
                        FailedCards['Card'].append(name)
                        FailedCards['Shunts'].append(sh)
                        FailedCards['Ranges'].append(r)
#                    c[counter].Update()
#                    c[counter].SaveAs("SummaryPlotsOutput/TOTAL_SHUNT_%.1f_.png"%(sh))
                    counter+=1
            outputText = open("%s_Failed_Shunts_and_Ranges.txt"%name,"w+")
            outputText.write(str(FailedCards))
            outputText.close()
#        totalbins[countbin].Write()
#        countbin+=1
        for tot in range(0, len(totalhist)-1):
            totalhist[tot].Draw()
            totalhist[tot].Write()
            c[-1].Update()
            c[-1].SaveAs("data/%s/Run_%s/SummaryPlots/TotalPlots/TOTAL_SHUNT_%.1f_.png"%(shunts[tot]))
            output.Close()
        return "Summary Plots Made!"
#################################################################################################################
    elif (arg == 'a'):
        xyz1234 = sqlite3.connect(database)
        cursor = xyz1234.cursor()
        name = database[database.find("_0x"):database.find(".")]
        # Modify rootout change title of output ROOT file
        rootout = name
        rootout = TFile("data/%s/Run_%s/SummaryPlots/summary_plot_%s.root" %(date, run, name), "recreate")
        for r in bins:
            counter=0
            for sh in shunts:
                if (r == 2 or r == 3) and (sh != 1):
                    continue
                # Fetch the values of slope and offset for the corresponding shunt and range
                values = cursor.execute("select slope,offset,QIE from qieshuntparams where range=%i and shunt=%.1f;" % (r, sh)).fetchall()
		#values = cursor.execute("select slope,offset, (SELECT slope from qieshuntparams where id=p.id and qie=p.qie and capID=p.capID and range=p.range and shunt=1) from qieshuntparams as p where range = %i and shunt = %.1f;"%(r,sh)).fetchall()
                # Fetch Max and minimum values

                
                
                maxmin = cursor.execute("select max(slope),min(slope) from qieshuntparams where range=%i and shunt = %.1f;" % (r, sh)).fetchall()
                maximum , minimum = maxmin[0]

                maximums  = max(plotBoundaries_slope[1]/sh, maximum+0.01)
                minimums  = min(plotBoundaries_slope[0]/sh, minimum-0.01)

                # if maxmin[0]==(None,None):
                #     maximums = .5
                #     minimums = 0
                # # SQLITE3 values are tuples, this turns the tuple into 2 numbers that can be used for ROOT arguments
                # else:
                #     maximums,minimums = shuntboundaries(maxmin[0],sh)
                #####################################
                # Makes a Canvas and histogram for the shunts that's added to the list
                c.append(TCanvas("Card %s Shunt %.1f  -  Range %i" % (name, sh, r), "histo"))
                c[-1].Divide(2,1)
                c[-1].cd(1)
                histshunt.append(TH1D("SLOPE Sh: %.1f - R: %i" %(sh, r),"%s Shunt %.1f - Range %i" % (name, sh, r), 100, minimums, maximums))
                histshunt[-1].SetTitle("SLOPE SH: %.1f R: %d"%(sh,r))
                histshunt[-1].GetXaxis().SetTitle("Slope")
                histshunt[-1].GetYaxis().SetTitle("Frequency")
                gPad.SetLogy(1)
                maxmin = cursor.execute("select max(offset),min(offset) from qieshuntparams where range=%i and shunt = %.1f;" % (r, sh)).fetchall()

                maximum, minimum = maxmin[0]
                
                maximumo  = max(plotBoundaries_offset[r], maximum)
                minimumo  = min(-1*plotBoundaries_offset[r], minimum)
                
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
                # if maxmin[0]>(offsetbin[r],-offsetbin[r]):
                #     maximumo = offsetbin[r]
                #     minimumo = -offsetbin[r]
                # else:
                #     maximumo=maximum+maximum*.2
                #     minimumo=minimum-minimum*.2
                # Make a Canvas and histogram for the offset that's added to the list
                #c2.append(TCanvas("%s OFFSET Shunt %.1f Range %i" % (name, sh, r), "histo"))
                c[-1].cd(2)
                histoffset.append(TH1D("OFFSET Sh: %.1f - R: %i" %(sh, r),"%s Shunt %.1f - Range %d" %(name, sh, r), 40, minimumo, maximumo))
                histoffset[-1].SetTitle("OFFSET SH: %.1f R: %d"%(sh,r))
                histoffset[-1].GetXaxis().SetTitle("Offset")
                histoffset[-1].GetYaxis().SetTitle("Frequency")
                gPad.SetLogy(1)
                # Fills the histograms with the values fetched above
                for val in values:
                    slope, offset, qie = val
                    c[-1].cd(1)
                    histshunt[-1].Fill(slope)
                    histshunt[-1].Draw()
                    c[-1].cd(2)
                    histoffset[-1].Fill(offset)
                    histoffset[-1].Draw()
                
                    hslopes[sh][r]['total'].Fill(slope)
                    hoffsets[sh][r]['total'].Fill(offset)
                    
                    if qie in backAdapter:
                        hslopes[sh][r]['back'].Fill(slope)
                        hoffsets[sh][r]['back'].Fill(offset)
                    else:
                        hslopes[sh][r]['front'].Fill(slope)
                        hoffsets[sh][r]['front'].Fill(offset)
                        
                #Write the histograms to the file, saving them for later
                #histshunt[-1].Draw()
                #histoffset[-1].Draw()
                #c2[-1].Write()
                c[-1].Update()
                #c[-1].SaveAs("data/%s/Run_%s/SummaryPlots/ImagesOutput/CARD_%s_SHUNT_%.1f_RANGE_%i.png"%(date, run, name, sh, r))
                c[-1].Write()
                maxmin = cursor.execute("select max(slope),min(slope) from qieshuntparams where range=%i and shunt = %.1f;" % (r, sh)).fetchall()
                maximum , minimum = maxmin[0]
                if sh == 1:
                    if 0.283 > minimum or maximum > 0.326:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 1.5:
                    if 0.185 > minimum or maximum > 0.22:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 2:
                    if 0.143 > minimum or maximum > 0.168:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 3:
                    if 0.095 > minimum or maximum > 0.115:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 4:
                    if 0.072 > minimum or maximum > 0.085:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 5:
                    if 0.0575 > minimum or maximum > 0.068:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 6:
                    if 0.048 > minimum or maximum > 0.064:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 7:
                    if 0.041 > minimum or maximum > 0.05:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 8:
                    if 0.036 > minimum or maximum > 0.044:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 9:
                    if 0.032 > minimum or maximum > 0.039:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 10:
                    if 0.029 > minimum or maximum > 0.035:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 11:
                    if 0.026 > minimum or maximum > 0.032:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if sh == 11.5:
                    if 0.025 > minimum or maximum > 0.031:
                        print "Card %s in Shunt %.1f in Range %i failed" % (name, sh, r)
                        failure = True
                if failure:
                    FailedCards['Card'].append(name)
                    FailedCards['Shunts'].append(sh)
                    FailedCards['Ranges'].append(r)
            countbin = 0
        
        
        rootout.Close()
        if len(FailedCards)>1:
            outputText = open("data/%s/Run_%s/SummaryPlots/Log/%s_Failed_Shunts_and_Ranges.txt"%(date,run,name),"w+")
            outputText.write(str(FailedCards))
            outputText.close()
        return "Summary Plots Made!"

def shuntboundaries(tuple1,sh):
    maxi , mini = tuple1
    maxis=0
    minis =0
    if sh == 0:
        if 0.28 > mini or maxi > 0.32:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .32
            minis = .28
    if sh == 1.5:
        if 0.185 > mini or maxi > 0.22:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .22
            minis = .185
    if sh == 2:
        if 0.143 > mini or maxi > 0.168:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .143
            minis = .168
    if sh == 3:
        if 0.095 > mini or maxi > 0.115:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .095
            minis = .115
    if sh == 4:
        if 0.072 > mini or maxi > 0.085:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .072
            minis = .085
    if sh == 5:
        if 0.0575 > mini or maxi > 0.068:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .05
            minis = .07
    if sh == 6:
        if 0.048 > mini or maxi > 0.064:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .048
            minis = .064
    if sh == 7:
        if 0.041 > mini or maxi > 0.05:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .041
            minis = .05
    if sh == 8:
        if 0.036 > mini or maxi > 0.044:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .036
            minis = .044
    if sh == 9:
        if 0.032 > mini or maxi > 0.039:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .032
            minis = .039
    if sh == 10:
        if 0.029 > mini or maxi > 0.035:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .029
            minis = .035
    if sh == 11:
        if 0.026 > mini or maxi > 0.032:
            maxis = maxi+(.1)
            minis = mini - (.1)
        else:
            maxis = .026
            minis = .032
    if sh == 11.5:
        if 0.025 > mini or maxi > 0.031:
            maxis = maxi+(.1)
            minis = mini-(.1)
        else:
            maxis = .025
            minis = .031
    return maxis,minis

dbnames = []
arg = ''
#ex: python SummaryPlots.py -c **.db
if (sys.argv[1] == '-t' or sys.argv[1] == '-total'):
    dbnames = glob.glob("data/%s/Run_%s/qieCalibrationParameters*.db"%(sys.argv[2],sys.argv[3]))
    arg = 't'
    data = 'eh'
    print SummaryPlot(data, arg, sys.argv[2], sys.argv[3])
    print "Completed Total"	
elif sys.argv[1]=='-a':
    arg = 'a'
    dbnames = glob.glob("data/%s/Run_%s/qieCalibrationParameters*.db"%(sys.argv[2],sys.argv[3]))
    for data in dbnames:
        print data
        print SummaryPlot(data, arg, sys.argv[2], sys.argv[3])
    print "Completed All"

    print "Making total plots"
    totals = TFile.Open("data/%s/Run_%s/SummaryPlots/summaryTotals.root"%(sys.argv[2],sys.argv[3]), "recreate")
    for sh in shunts:
        for r in xrange(4):
            if r > 1 and sh != 1: continue
            hslopes[sh][r]['total'].Write()
            hslopes[sh][r]['front'].Write()
            hslopes[sh][r]['back'].Write()
            hoffsets[sh][r]['total'].Write()
            hoffsets[sh][r]['front'].Write()
            hoffsets[sh][r]['back'].Write()
    totals.Close()

    with open("data/%s/Run_%s/SummaryPlots/pickle_summaryTotals.p"%(sys.argv[2],sys.argv[3]), "wb") as f:
        pickle.dump(hslopes, f)
        pickle.dump(hoffsets, f)
    
    rundir = "data/%s/Run_%s/SummaryPlots" % (sys.argv[2], sys.argv[3])
    outdir = "adapterTests"
    os.system("mkdir -p %s/%s" % (rundir, outdir))
    c = TCanvas("c","c",1600,1200) 
    shunts = [1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11.5]
    ranges = xrange(4)
    gStyle.SetOptStat(0)
    for r in ranges:
        for sh in shunts:
            if sh > 1 and r > 1: continue
            l = TLegend(0.75, 0.75, 0.9, 0.9)
            l.AddEntry(hslopes[sh][r]['front'], "Front adapter")
            l.AddEntry(hslopes[sh][r]['back'], "Back adapter")

            hslopes[sh][r]['front'].SetLineColor(kRed)
            hslopes[sh][r]['front'].SetLineWidth(2.0)
            hslopes[sh][r]['back'].SetLineColor(kBlue)
            hslopes[sh][r]['back'].SetLineWidth(2.0)

            hslopes[sh][r]['back'].SetTitle("Slopes  Shunt %.1f Range %d" % (sh,r))
            hslopes[sh][r]['back'].Draw("HIST")
            hslopes[sh][r]['front'].Draw("HIST SAME")
            l.Draw("SAME")
            c.SaveAs("%s/%s/slopes_shunt_%s_range_%d.png" % (rundir,outdir,str(sh).replace(".","_"),r))

            lo = TLegend(0.75, 0.75, 0.9, 0.9)
            lo.AddEntry(hslopes[sh][r]['front'], "Front adapter")
            lo.AddEntry(hslopes[sh][r]['back'], "Back adapter")

            hoffsets[sh][r]['front'].SetLineColor(kRed)
            hoffsets[sh][r]['front'].SetLineWidth(2.0)
            hoffsets[sh][r]['back'].SetLineColor(kBlue)
            hoffsets[sh][r]['back'].SetLineWidth(2.0)

            hoffsets[sh][r]['back'].SetTitle("Offsets  Shunt %.1f Range %d" %(sh,r))
            hoffsets[sh][r]['back'].Draw("HIST")
            hoffsets[sh][r]['front'].Draw("HIST SAME")
            lo.Draw("SAME")
            c.SaveAs("%s/%s/offsets_shunt_%s_range_%d.png" % (rundir,outdir,str(sh).replace(".","_"),r))

else:
     dbnames = glob.glob("data/%s/Run_%s/qieCalibrationParameters*.db"%(sys.argv[2],sys.argv[3]))
     database = sys.argv[1]
     print SummaryPlot(database, arg, sys.argv[2], sys.argv[3])
     print "Completed N?A"	    
#from SummaryPlots import SummaryPlot
