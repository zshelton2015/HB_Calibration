#!/usr/bin/env python
import ROOT
from ROOT import TFile, TLegend, TCanvas, gROOT, kOrange, kBlack, kBlue, kCyan, kViolet, kGreen, kRed, TLatex, TGraph, TGraphErrors, TGraphAsymmErrors, TPad
from ROOT import gStyle
from array import array
from math import sqrt
from optparse import OptionParser
import os
import sys
from linearADC import linADC
gStyle.SetOptStat("imr")

colors = [kRed, kOrange+1, kGreen+1, kBlack, kCyan, kBlue, kViolet-1]

#############################################
#  Quiet                                    #
#  Usage: Quiets info, warnings, or errors  #
#                                           #
#  Ex: TCanvas.c1.SaveAs("myplot.png")      #
#      Quiet(c1.SaveAs)("myplot.png")       #
#############################################
def Quiet(func, level = ROOT.kInfo + 1):
    def qfunc(*args,**kwargs):
        oldlevel = ROOT.gErrorIgnoreLevel
        ROOT.gErrorIgnoreLevel = level
        try:
            return func(*args,**kwargs)
        finally:
            ROOT.gErrorIgnoreLevel = oldlevel
    return qfunc


def plotQIcalibration(results, outDir = "results", currentMode = ""):
    gROOT.SetBatch(True)
    calibGraphs = []
    gStyle.SetMarkerColor(kBlue)
    gStyle.SetLineColor(kBlack)
    

    #for ch in xrange(1, len(results)+1):   # Number of channels
    for ch in sorted(results.keys()): 
        gr = TGraphAsymmErrors()
        gr.SetMarkerStyle(22)
        gr.SetMarkerSize(1.2)
        gr.SetName("Channel_%d_Charge_vs_DAC" % ch)
        gr.SetTitle("Channel %d  Charge vs DAC value%s" % (ch, "  %s current mode" % currentMode if currentMode in ["low", "high"] else ""))
        

        res = results[ch]
        for i, dacVal in enumerate(sorted(res.keys())):
            mean = res[dacVal]["mean"] * 25.e6  # Convert to fC
            err = res[dacVal]["std"] * 25.e6
   
            # Index of new point
            np = gr.GetN()
            
            # Set value and error
            gr.SetPoint(np, dacVal, mean)
            gr.SetPointError(np, 0., 0., err, err)
 
        calibGraphs.append((gr,ch))

    if outDir[-1] == "/": outDir = outDir[:-1]
    os.system("mkdir -p %s/calibGraphs" % outDir )

    c1 = TCanvas('c1','c1', 1200, 800)
    c1.SetLeftMargin(0.15);
    c1.SetRightMargin(0.25)
    c1.SetBottomMargin(0.25);
    pad1=TPad('p1','p1',0.,0.,1.0,1.0)
    pad1.Draw()

    outF = TFile.Open(outDir + "/calibration.root", "RECREATE")

    fitParams = {}   # Converted to charge by * 25ns

    for i,(gr,ch) in enumerate(calibGraphs):
        gr.Fit('pol1', "Q")   # Q: Quiet mode
        f = gr.GetFunction("pol1")
        p0 = f.GetParameter(0)
        p0_err = f.GetParError(0)
        p1 = f.GetParameter(1)
        p1_err = f.GetParError(1)
        
        fitline = "offset %g #pm %g   slope %g #pm %g" % (p0, p0_err, p1, p1_err)
        
        # Convert to fC
        fitParams[ch] = {"slope":(p1), "offset":(p0)}
        #fitParams[(i+1)] = {"slope":(p1), "offset":(p0)}
        

        gr.GetXaxis().SetTitle("DAC value")
        gr.GetYaxis().SetTitle("Charge [fC]")
        if currentMode == "low":
            gr.GetYaxis().SetTitleOffset(1.37)

        pad1.cd()
        gr.Draw("AP")
        gr.Write()
        txt=TLatex()
        txt.SetNDC(True)
        txt.SetTextFont(43)
        txt.SetTextSize(20)
        txt.SetTextAlign(12)
        txt.DrawLatex(0.40,0.87, fitline)
        Quiet(c1.SaveAs)(outDir + "/calibGraphs/channel_%d.png" % (i+1))
    
#    for g in adcGraphs:
 #       
  #      g.Write()

   # for g in chargeGraphs:
    #    g.Write()

    #outF.Write()
    outF.Close()
    return fitParams


def plotHistos(dac, histVals, qiCalib = None, outDir = "results", currentMode = ""):
    adcGraphs = []
    chargeGraphs = []
    gStyle.SetMarkerColor(kBlue)
    gStyle.SetLineColor(kBlack)
    
    convFactor = 1.
    if qiCalib is None:
        # Use nominal qiCalib
        print "Using nominal QI calibrations"
        if currentMode == "low":
            convFactor = 1.375
        elif currentMode == "high":
            convFactor = 7.7
        offset = 0.

    else:
        print "Using custom QI calibrations"

    #for i in range(len(histVals[dac[0]])):
    for i in range(12):
        adcGr = TGraphAsymmErrors()
        adcGr.SetMarkerStyle(22)
        #adcGr.SetMarkerSize(1.0)
        adcGr.SetName("h%d_ADC" % i)
        adcGr.SetTitle("h%d  ADC vs %s" % (i, "Charge  %s current mode" % currentMode if currentMode in ["low", "high"] else "DAC value"))
        
        chGr = TGraphAsymmErrors()
        chGr.SetMarkerStyle(22)
        #chGr.SetMarkerSize(1.3)
        chGr.SetName("h%d_LinADC" % i)
        chGr.SetTitle("h%d  Lin ADC vs %s" % (i, "Charge  %s current mode" % currentMode if currentMode in ["low", "high"] else "DAC value"))
        adcGraphs.append(adcGr)
        chargeGraphs.append(chGr)


    for i, dv in enumerate(dac):
        for n in range(len(adcGraphs)):
            mean = histVals[dv][n]["mean"]
            err = histVals[dv][n]["rms"]
   
            if qiCalib is not None:
                QIchan = int(n/6)*8 + n%6 + 1 
                convFactor = qiCalib[QIchan]["slope"]
                offset = qiCalib[QIchan]["offset"]
            # Index of new point
            np = adcGraphs[n].GetN()
            
            # Set value and error
            adcGraphs[n].SetPoint(np, dv*convFactor + offset, mean)
            adcGraphs[n].SetPointError(np, 0., 0., err, err)

            chMean, chErr = linADC(mean, err)

            chargeGraphs[n].SetPoint(np, dv*convFactor + offset, chMean)
            chargeGraphs[n].SetPointError(np, 0., 0., chErr, chErr)


    if outDir[-1] == "/": outDir = outDir[:-1]
    os.system("mkdir -p %s/adcH; mkdir -p %s/chargeH" % (outDir, outDir) )

    c1 = TCanvas('c1','c1', 1200, 800)
    c1.SetLeftMargin(0.15);
    c1.SetRightMargin(0.25)
    c1.SetBottomMargin(0.25);
    pad1=TPad('p1','p1',0.,0.,1.0,1.0)
    pad1.Draw()

    outF = TFile.Open(outDir + "/histos.root", "RECREATE")

    xAxisTitle = "Charge [fC]" if currentMode in ["low", "high"] else "DAC value"

    for i,adcGr in enumerate(adcGraphs):
        """
        adcGr.Fit('pol1', "Q")  # Q: Quiet mode
        f = adcGr.GetFunction("pol1")
        p0 = f.GetParameter(0)
        p0_err = f.GetParError(0)
        p1 = f.GetParameter(1)
        p1_err = f.GetParError(1)
        
        fitline = "offset %.3f #pm %.2f   slope %.3f #pm %.6f" % (p0, p0_err, p1, p1_err)
        """
        adcGr.GetXaxis().SetTitle(xAxisTitle)
        adcGr.GetYaxis().SetTitle("ADC")
        adcGr.GetYaxis().SetTitleOffset(1.2)
        pad1.cd()
        pad1.SetLogx(True)
        adcGr.Draw("AP")
        adcGr.Write()
        Quiet(c1.SaveAs)(outDir + "/adcH/adc_hist_%d.png" % i)

    c1.SetLogy(True)

    for i,chGr in enumerate(chargeGraphs):
        chGr.Fit('pol1', "Q")   # Q: Quiet mode
        f = chGr.GetFunction("pol1")
        p0 = f.GetParameter(0)
        p0_err = f.GetParError(0)
        p1 = f.GetParameter(1)
        p1_err = f.GetParError(1)
        
        fitline = "offset %.3f #pm %.2f   slope %.3f #pm %.6f" % (p0, p0_err, p1, p1_err)

        chGr.GetXaxis().SetTitle(xAxisTitle)
        chGr.GetYaxis().SetTitle("Linearized ADC")
        chGr.GetYaxis().SetTitleOffset(1.2)

        pad1.cd()
        pad1.SetLogx(True)
        pad1.SetLogy(True)
        chGr.Draw("AP")
        chGr.Write()
        txt=TLatex()
        txt.SetNDC(True)
        txt.SetTextFont(43)
        txt.SetTextSize(20)
        txt.SetTextAlign(12)
        txt.DrawLatex(0.45,0.87, fitline)
        Quiet(c1.SaveAs)(outDir + "/chargeH/charge_hist_%d.png" % i)
    
#    for g in adcGraphs:
 #       
  #      g.Write()

   # for g in chargeGraphs:
    #    g.Write()

    #outF.Write()
    outF.Close()




def main():
    gROOT.SetBatch(True)  # True: Don't display canvas
    usage = 'usage: %prog [options]'
    parser = OptionParser(usage) 
    parser.add_option("-i", "--inF", dest = 'inF', help="input file")
    parser.add_option("-o", dest = 'outF', default="plots.root", help="output root file")
    (opt, args) = parser.parse_args()

    dac = []
    currentLow = []
    currentHigh = []

    try:
        with open(opt.inF, 'r') as f:
            for i,line in enumerate(f):
                data = line.split()
                #print "line %d\t%s" % (i, data)
                if len(data) < 1: continue

                dac.append(int(data[0]))
                currentLow.append ([float(data[1]), float(data[2])] )
                
                if len(data) > 4:
                    currentHigh.append ([float(data[3]), float(data[4])] )
    except IOError:
        print "Unable to open file %s!" % opt.inF
        sys.exit()
    except:
        print "Error parsing file %s!" % opt.inF
        sys.exit()

    currentLowG = makePlot(dac, currentLow, "Current-low") 
    currentHighG = makePlot(dac, currentHigh, "Current-high") 
    
    slopeL = currentLowG.GetFunction("pol1").GetParameter(1)
    slopeH = currentHighG.GetFunction("pol1").GetParameter(1)

    print "\nRatio of slopes (high/low):", slopeH/slopeL
    
    outFile = TFile.Open(opt.outF, "RECREATE")
    currentLowG.Write()
    currentHighG.Write()

    outFile.Close()


if __name__ == "__main__":
    sys.exit(main())
