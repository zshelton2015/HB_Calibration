#!/usr/bin/env python
import ROOT
from ROOT import TFile, TLegend, TCanvas, gROOT, kOrange, kBlack, kBlue, kCyan, kViolet, kGreen, kRed, TLatex, TGraph, TGraphErrors, TGraphAsymmErrors, TPad
from ROOT import gStyle
from array import array
from argparse import ArgumentParser
import os
import sys
from linearADC import linADC
import pickle

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


def plotQIEnoise(proto, new, dacVal, current, outDir = "noisePlots", channels = range(1,17)):
    if channels == range(1,17): 
        nChan = len(proto)
        protoGr = [TGraphErrors(nChan, array('d', [-0.1 + ch for ch in channels]), array('d', [proto[ch][capID]["mean"] for ch in channels]), array('d', [0.]*nChan), array('d', [proto[ch][capID]["rms"] for ch in channels])) for capID in xrange(len(proto[min(channels)]))]
        newGr = [TGraphErrors(nChan, array('d', [0.1 + ch for ch in channels]), array('d', [new[ch][capID]["mean"] for ch in channels]), array('d', [0.]*nChan), array('d', [new[ch][capID]["rms"] for ch in channels])) for capID in xrange(len(new[min(channels)]))]
        l = [TLegend(0.75, 0.75, 0.95, 0.95) for i in xrange(len(proto[min(channels)]))] 
    else:
        nChan = len(channels)
        protoGr = [TGraphErrors(nChan, array('d', channels), array('d', [proto[ch][capID]["mean"] for ch in channels]), array('d', [0.]*nChan), array('d', [proto[ch][capID]["rms"] for ch in channels])) for capID in xrange(len(proto[min(channels)]))]
        newGr = [TGraphErrors(nChan, array('d', [0.1 + ch for ch in channels]), array('d', [new[ch][capID]["mean"] for ch in channels]), array('d', [0.]*nChan), array('d', [new[ch][capID]["rms"] for ch in channels])) for capID in xrange(len(new[min(channels)]))]
        l = [TLegend(0.75, 0.75, 0.95, 0.95) for i in xrange(len(proto[min(channels)]))] 

    for capID in xrange(4):
        protoGr[capID].SetMarkerColor(kBlue)
        protoGr[capID].SetMarkerStyle(22)
        protoGr[capID].SetLineColor(kBlue)
        newGr[capID].SetMarkerColor(kRed)
        newGr[capID].SetMarkerStyle(22)
        newGr[capID].SetLineColor(kRed)
        protoGr[capID].SetTitle("QIE Charge  DAC %d  CapID %d  %s current mode" % (dacVal, capID, current))
        #protoGr[capID].GetXaxis().SetRangeUser(0.5, len(proto)+0.5)
        if channels == range(1,17):
            protoGr[capID].GetXaxis().SetNdivisions(2*nChan)
            protoGr[capID].GetXaxis().SetRangeUser(min(channels)-0.5, max(channels)+0.5)
            protoGr[capID].GetXaxis().SetTitle("Channel")
        else:
            protoGr[capID].SetTitle("QIE Charge  Channel %d  DAC %d  CapID %d  %s current mode" % (channels[0], dacVal, capID, current))
            protoGr[capID].SetMarkerSize(2.0)
            newGr[capID].SetMarkerSize(2.0)
            #protoGr[capID].GetXaxis().SetNdivisions(0)
            #protoGr[capID].GetXaxis().SetRangeUser(min(channels)-0.5, max(channels)+0.5)
            #protoGr[capID].GetXaxis().SetRangeUser(0.5, 1.5)
            if current == "low":
                protoGr[capID].GetYaxis().SetRangeUser(15, 25)
            else:
                protoGr[capID].GetYaxis().SetRangeUser(50, 60)


        protoGr[capID].GetYaxis().SetTitle("ADC")
        l[capID].AddEntry(protoGr[capID], "Prototype Adapter", "pl")
        l[capID].AddEntry(newGr[capID], "New Adapter", "pl")
        #l[capID].AddEntry(protoGr[capID], "Only Ch %d" % channels[0], "pl")
        #l[capID].AddEntry(newGr[capID], "All Ch", "pl")
      
    
    #l = TLegend(0.75, 0.75, 0.95, 0.95)
    #l.AddEntry(protoGr[0], "Prototype Adapter")
    #l.AddEntry(newGr, "New Adapter")

    if outDir[-1] == "/": outDir = outDir[:-1]
    os.system("mkdir -p %s" % outDir )

    c1 = TCanvas('c1','c1', 1200, 800)
    c1.SetLeftMargin(0.15);
    c1.SetRightMargin(0.25)
    c1.SetBottomMargin(0.25);
    pad1=TPad('p1','p1',0.,0.,1.0,1.0)
    pad1.Draw()

    outF = TFile.Open("%s/QIEnoise_dac%d_%s.root" % (outDir, dacVal, current), "RECREATE")
    for capID in xrange(4):
        c1.Clear()
        protoGr[capID].Draw("AP")
        newGr[capID].Draw("P SAME")
        l[capID].Draw("SAME")
        protoGr[capID].Write("capID%d_proto"%capID)
        newGr[capID].Write("capID%d_new"%capID)
            
        Quiet(c1.SaveAs)("%s/QIEnoise_dac%d_CapID%d_%s.png" % (outDir, dacVal, capID, current))
        
    outF.Close()
    return protoGr, newGr


def main():
    #gROOT.SetBatch(True)  # True: Don't display canvas
    parser = ArgumentParser("plotQIEnoise.py") 
    parser.add_argument("-p", dest="proto", help="prototype adapter histo file")
    parser.add_argument("-n", dest="new", help="new adapter histo file")
    parser.add_argument("-m", dest="current", metavar="[low,high]", help="current mode (low or high)")
    parser.add_argument("-c", "--channel", dest="channel", default = -1, type=int, help="channel to plot [1-16]")
    parser.add_argument("-d", "--dacVal", dest="dacVal", type=int, help="dac value")
    parser.add_argument("-o", dest = 'outDir', default="QIEnoise", help="output root file")
    args = parser.parse_args()
    print args
    dac = []
    currentLow = []
    currentHigh = []
    if args.channel == -1:
        channels = range(1,17)
    elif args.channel not in range(1,17):
        print "Channel %d invalid. Choose from [1-16]"
        sys.exit()
    else:
        channels = [args.channel]

    protoF = TFile.Open(args.proto, "read")
    newF = TFile.Open(args.new, "read")
    protoH = {}
    newH = {}
    for ch in channels:
        ph = eval("protoF.Get('h%d').Clone()" % (ch-1))
        ph.SetDirectory(0)
        protoH[ch] = ph
        
        nh = eval("newF.Get('h%d').Clone()" % (ch-1))
        nh.SetDirectory(0)
        newH[ch] = nh

    protoF.Close()
    newF.Close()

    #proto = [{}] * nChan
    #new = [{}] * nChan
    proto = {}
    new = {}
    # Separate by capID and evaluate mean/rms
    for ch in channels:
        proto[ch] = {}
        new[ch] = {}
        for capID in xrange(4):
            offset = 64 * capID
            protoH[ch].GetXaxis().SetRangeUser(offset, offset+63)
            newH[ch].GetXaxis().SetRangeUser(offset, offset+63)
            proto[ch][capID] = {"mean":(protoH[ch].GetMean() - offset), "rms":protoH[ch].GetRMS()}
            new[ch][capID] = {"mean":(newH[ch].GetMean() - offset), "rms":newH[ch].GetRMS()}
   
    plotQIEnoise(proto, new, args.dacVal, args.current, args.outDir, channels)


if __name__ == "__main__":
    sys.exit(main())
