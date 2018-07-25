#!/usr/bin/env python
from ROOT import *
import sys
import os
import json
import glob
import fnmatch
import numpy
from array import array
from pprint import pprint
from collections import Counter

gROOT.SetBatch(True)
gROOT.SetStyle("Plain")

try:
    Quiet(TObject())
except NameError:
    from utils import Quiet

def saveTGraph(rootFile,shuntMult,i_range,qieNumber,i_capID,verbose=False):
    tGraphDir = rootFile.Get("LinadcVsCharge")
    fitLineDir = rootFile.Get("fitLines")
    fName = rootFile.GetName()
    outputDir = os.path.dirname(fName)


    gName = "LinADCvsfC_%s_range_%s_shunt_%s_capID_%s_linearized"%(qieNumber,i_range,str("%.1f"%shuntMult).replace(".","_"),i_capID)

    graph = tGraphDir.Get(gName)

    fitLine = fitLineDir.Get("fit_%s"%gName)

    qieInfo = ""

    qieBarcode = ""
    qieUniqueID = ""

    useCalibrationMode = True
    saveName = outputDir
    if saveName[-1]!='/':
        saveName += '/'
    saveName += "plots"

    if qieBarcode != "":
        qieInfo += ", Barcode " + qieBarcode

    if qieUniqueID != "": 
        qieInfo += "  UID "+qieUniqueID
    else:
        qieUniqueID = "UnknownID"

    #saveName += qieUniqueID
    if not os.path.exists(saveName):
        os.system("mkdir -p %s"%saveName)
    saveName += "/LinADCvsfC"
    if qieNumber != 0:
        qieInfo += ", QIE " + str(qieNumber)
        saveName += "_qie"+str(qieNumber)

    qieInfo += ", CapID " + str(i_capID)
    saveName += "_range"+str(i_range)
    saveName += "_capID"+str(i_capID)
    saveName += "_shunt_"+str(shuntMult).replace(".","_")
    if not useCalibrationMode: saveName += "_NotCalMode"
    saveName += ".png"
    graph.SetTitle("LinADC vs Charge, Range %i Shunt %s%s" % (i_range,str(shuntMult).replace(".","_"),qieInfo))
    graph.GetYaxis().SetTitle("Lin ADC")
    graph.GetYaxis().SetTitleOffset(1.2)
    graph.GetXaxis().SetTitle("Charge fC")
    xVals = graph.GetX()
    exVals = graph.GetEX()
    yVals = graph.GetY()
    eyVals = graph.GetEY()
    residuals = []
    residualErrors = []
    #residualsY = []
    #residualErrorsY = []
    eUp = []
    eDown = []
    N = graph.GetN()
    x = []
    y = []

    for i in range(N):
        residuals.append((yVals[i]-fitLine.Eval(xVals[i])))
        xLow = (xVals[i]-exVals[i])
        xHigh = (xVals[i]+exVals[i])
        residualErrors.append((eyVals[i]))
        x.append(xVals[i])


    resArray = array('d',residuals)
    resErrArray = array('d',residualErrors)
    resErrUpArray = array('d',eUp)
    resErrDownArray = array('d',eDown)
    xArray = array('d',x)
    xErrorsArray = array('d',[0]*len(x))

    if verbose and i_range == 1:
        print  "the length of residuals are:",len(resArray)
        print "the charge length :",len(x)

    residualGraphX = TGraphErrors(len(x),xArray,resArray, xErrorsArray, resErrArray)

    residualGraphX.SetTitle("")
    c1 = TCanvas()
    p1 = TPad("","",0,0.2,0.9,1)
    p2 = TPad("","",0.,0.,0.9,0.2)
    p1.Draw()
    p2.Draw()
    p1.SetFillColor(kWhite)
    p2.SetFillColor(kWhite)
    p1.cd()
    p1.SetBottomMargin(0)
    p1.SetRightMargin(0)
    p2.SetTopMargin(0)
    p2.SetBottomMargin(0.3)
    graph.Draw("ap")
    fitLine.SetLineColor(kRed)
    fitLine.SetLineWidth(1)
    fitLine.Draw("same")

    xmin = graph.GetXaxis().GetXmin()
    xmax = graph.GetXaxis().GetXmax()
    ymin = graph.GetYaxis().GetXmin()
    ymax = graph.GetYaxis().GetXmax()
    text = TPaveText(xmin + (xmax-xmin)*.2, ymax - (ymax-ymin)*(.3),xmin + (xmax-xmin)*.6,ymax-(ymax-ymin)*.1)
    text.SetFillColor(kWhite)
    text.SetTextSize(0.75*text.GetTextSize())
    text.SetFillStyle(8000)
    ######### Add in Cut Values #############
    text.AddText("Slope =  %.4f +- %.4f LinADC/fC [%.4f,%.4f]" % (fitLine.GetParameter(1), fitLine.GetParError(1),failureconds[shuntMult][0],failureconds[shuntMult][1]))
    text.AddText("Offset =  %.2f +- %.2f LinADC [%.1f,.1f]" % (fitLine.GetParameter(0), fitLine.GetParError(0),failcondo[i_range][0],-1*failcondo[i_range][0]))
    text.AddText("Chisquare = %e " % (fitLine.GetChisquare()))
    text.Draw("same")


    p2.cd()
    p2.SetTopMargin(0)
    p2.SetRightMargin(0)
    p2.SetBottomMargin(0.35)
    residualGraphX.Draw("ap")
    zeroLine = TF1("zero","0",-9e9,9e9)
    zeroLine.SetLineColor(kBlack)
    zeroLine.SetLineWidth(1)
    zeroLine.Draw("same")

    # xmin = xmin-10
    # xmax = xmax+10
    #if minCharge < 10: minCharge = -10

    graph.GetXaxis().SetRangeUser(xmin*0.9, xmax*1.1)
    graph.GetYaxis().SetRangeUser(ymin*.9,ymax*1.1)

    residualGraphX.GetXaxis().SetRangeUser(xmin*0.9, xmax*1.1)
    residualGraphX.GetYaxis().SetRangeUser(-0.1,0.1)
    residualGraphX.SetMarkerStyle(7)
    residualGraphX.GetYaxis().SetNdivisions(3,5,0)


    residualGraphX.GetXaxis().SetLabelSize(0.15)
    residualGraphX.GetYaxis().SetLabelSize(0.15)
    residualGraphX.GetYaxis().SetTitle("Residuals")
    residualGraphX.GetXaxis().SetTitle("Charge (fC)")
    residualGraphX.GetXaxis().SetTitleSize(0.15)
    residualGraphX.GetYaxis().SetTitleSize(0.15)
    residualGraphX.GetYaxis().SetTitleOffset(0.33)

    p1.cd()

    if not verbose:
        Quiet(c1.SaveAs)(saveName)
    else:
        c1.SaveAs(saveName)
    #c1.SaveAs(saveName)

def saveOnFail(inputDir):
    fileList = []
    for root,dirnames,filenames in os.walk(os.path.join(inputDir,"Submission")):
        for filename in fnmatch.filter(filenames,'*.json'):
            fileList.append(os.path.join(root,filename))

    for fName in fileList:
        rootFile = TFile.Open(fName.replace(".json",".root").replace("70/","70/fitResults_"),'read')

        outputDir = os.path.dirname(fName)
        ###################################################
        # Values to get from json file
        ###################################################
        qieBarcode = ""
        qieUniqueID = ""
        qieNumber = 1
        i_capID = 0
        i_range = 0
        shuntMult = 1
        useCalibrationMode = True
        verbose = False


        ###################################################
        # Getting Values From json
        ###################################################
        inFile = open(fName,"r")

        jsonFile = json.load(inFile)


        qieUniqueID = os.path.splitext(os.path.basename(fName))[0]

        if jsonFile['Result']:
            continue


        failModeList = []
        for failModeOffset in jsonFile['Comments']['Offset']:
            if failModeOffset not in failModeList:
                failModeList.append(failModeOffset)
        for failModeSlope in jsonFile['Comments']['Slope']:
            if failModeSlope not in failModeList:
                failModeList.append(failModeSlope)
        for failModeFit in jsonFile['Comments']['Poor fit']:
            if failModeFit not in failModeList:
                failModeList.append(failModeFit)

        qieList = [x[2] for x in failModeList]
        qieCounter = Counter(qieList)

        tooManyErrors = []
        for badChip in qieCounter:
        #    print badChip,": ",qieCounter[badChip]
            if qieCounter[badChip] >= 16:
                saveName = outputDir
                if saveName[-1]!='/':
                    saveName += '/'
                saveName += "plots"
                saveName += "/LinADCvsfC"
                if qieNumber != 0: 
                    saveName += "_qie"+str(badChip)

                saveName += ".png"
                canv = TCanvas("c")
                text = TPaveText(0.05,0.1,0.95,0.8)
                text.AddText("QIE %s Contains More Than 16 Errors!"%badChip)
                text.GetListOfLines().Last().SetTextColor(2)
                if verbose:
                    print "%s QIE %s Contains More That 16 Errors!"%(qieUniqueID,badChip)
                text.Draw()
                canv.Update()
                if not verbose:
                    Quiet(canv.SaveAs)(saveName)
                else:
                    canv.SaveAs(saveName)
                failModeList = [failMode for failMode in failModeList if failMode[2] != badChip]


        for failMode in failModeList:

            shuntMult, i_range, qieNumber, i_capID = failMode
            saveTGraph(rootFile,shuntMult,i_range,qieNumber,i_capID)

if __name__ == '__main__':
    saveOnFail(sys.argv[1])
