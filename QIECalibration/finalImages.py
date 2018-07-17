import ROOT as r
from selectionCuts import *
import sys
import glob
import os
from shutil import copyfile

r.gROOT.SetBatch(True)

import json

def finalImages(dirName=""):
    # Initialize Range and Shunt values
    ranges = [0,1,2,3]
    shunts = [1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11.5]


    # Get list of fit root files
    fileList = glob.glob(os.path.join(dirName,"fitResults*.root"))
        
    for fileName in fileList:
       
        # Parse uid from file name
        
	uid = fileName[fileName.find("fitResults_")+11:fileName.find(".root")]

    
        #Create output directory if it doesn't already exist
        cardDir = os.path.join(dirName,"Submission/Card_%s"%(uid))
        outDir = os.path.join(dirName,"Submission/Card_%s/plots"%(uid))
        if not os.path.exists(outDir):
            os.makedirs(outDir)
    
        # Copy other output files to submission directories
        copyfile(os.path.join(dirName,"fitResults_%s.root"%uid),os.path.join(cardDir,"fitResults_%s.root"%uid))
        copyfile(os.path.join(dirName,"qieCalibrationParameters_%s.db"%uid),os.path.join(cardDir,"qieCalibrationParameters_%s.db"%uid))
        copyfile(os.path.join(dirName,"SummaryPlots/%s/%s.json"%(uid,uid)),os.path.join(cardDir,"%s.json"%uid))
    
        # Open ROOT file and get the Summary Plots directory
        rootfile = r.TFile(fileName,"READ")
        sumDir = rootfile.Get("SummaryPlots")
        
        # Initialize vertical lines for pass/fail boundaries
        hline = r.TLine(0,0,0,0)
        hline.SetLineColor(2)
        lline = r.TLine(0,0,0,0)
        lline.SetLineColor(2)
        loline = r.TLine(0,0,0,0)
        loline.SetLineColor(2)
        holine = r.TLine(0,0,0,0)
        holine.SetLineColor(2)
    
        for sh in shunts:
            # If shunt 1, loop over all ranges
            if sh == 1:
                canv = r.TCanvas("c1","c1",1800,700)
                canv.Divide(4,2)
                for ra in ranges:
                    #Draw Slope Histogram with boundary lines, excluding the drawing if the histogram doesn't exist
                    canv.cd(ra+1)
                    if sumDir.GetListOfKeys().Contains("SLOPE_Sh_%s_R_%d"%(str(sh).replace(".",""),ra)):
                        hist = sumDir.Get("SLOPE_Sh_%s_R_%d"%(str(sh).replace(".",""),ra))
                        hist.Draw()
                        hline.DrawLine(failureconds[sh][1],0,failureconds[sh][1],hist.GetMaximum()+1)
                        hline.Draw("same")
                        lline.DrawLine(failureconds[sh][0],0,failureconds[sh][0],hist.GetMaximum()+1)
                        lline.Draw("same")
                    #Draw Offset Histogram with boundary lines, excluding the drawing if the histogram doesn't exist
                    canv.cd(ra+1+4)
                    if sumDir.GetListOfKeys().Contains("OFFSET_Sh_%s-R_%d"%(str(sh).replace(".",""),ra)):
                        hist = sumDir.Get("OFFSET_Sh_%s-R_%d"%(str(sh).replace(".",""),ra))
                        hist.Draw()
                        holine.DrawLine(failcondo[ra][0],0,failcondo[ra][0],hist.GetMaximum()+1)
                        holine.Draw("same")
                        loline.DrawLine(-failcondo[ra][0],0,-failcondo[ra][0],hist.GetMaximum()+1)
                        loline.Draw("same")
                # Save canvas as png
                canv.SaveAs(os.path.join(outDir,"Shunt_%s_%s.png"%(str(sh).replace(".",""),uid)))
            # If not shunt 1, only loop over ranges 0 and 1
            else:
                canv = r.TCanvas("c1","c1",900,700)
                canv.Divide(2,2)
                for ra in [0,1]:
                    #Draw Slope Histogram with boundary lines, excluding the drawing if the histogram doesn't exist
                    canv.cd(ra+1)
                    if sumDir.GetListOfKeys().Contains("SLOPE_Sh_%s_R_%d"%(str(sh).replace(".",""),ra)):
                        hist = sumDir.Get("SLOPE_Sh_%s_R_%d"%(str(sh).replace(".",""),ra))
                        hist.Draw()
                        hline.DrawLine(failureconds[sh][1],0,failureconds[sh][1],hist.GetMaximum()+1)
                        hline.Draw("same")
                        lline.DrawLine(failureconds[sh][0],0,failureconds[sh][0],hist.GetMaximum()+1)
                        lline.Draw("same")
                    #Draw Offset Histogram with boundary lines, excluding the drawing if the histogram doesn't exist
                    canv.cd(ra+1+2)
                    if sumDir.GetListOfKeys().Contains("OFFSET_Sh_%s-R_%d"%(str(sh).replace(".",""),ra)):
                        hist = sumDir.Get("OFFSET_Sh_%s-R_%d"%(str(sh).replace(".",""),ra))
                        hist.Draw()
                        holine.DrawLine(failcondo[ra][0],0,failcondo[ra][0],hist.GetMaximum()+1)
                        holine.Draw("same")
                        loline.DrawLine(-failcondo[ra][0],0,-failcondo[ra][0],hist.GetMaximum()+1)
                        loline.Draw("same")
                canv.SaveAs(os.path.join(outDir,"Shunt_%s_%s.png"%(str(sh).replace(".",""),uid)))
                        
        rootfile.Close()
if __name__ == '__main__':
    finalImages(sys.argv[1])
