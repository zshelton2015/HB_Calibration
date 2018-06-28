from ROOT import *


def fillFitUncertaintyHists(summaryFile, verbose = False):
    range0Unc = TH1F("SlopeUncertainty_Range0","SlopeUncertainty_Range0",100,0,.05)
    range1Unc = TH1F("SlopeUncertainty_Range1","SlopeUncertainty_Range1",100,0,.05)
    range2Unc = TH1F("SlopeUncertainty_Range2","SlopeUncertainty_Range2",100,0,.05)
    range3Unc = TH1F("SlopeUncertainty_Range3","SlopeUncertainty_Range3",100,0,.05)

    _file = TFile.Open(summaryFile,"update")
    keys = _file.GetDirectory("fitLines").GetListOfKeys()

    badfits = []

    for k in keys:
        fitline = k.ReadObj()
        slopeUnc = 1
        if fitline.GetParameter(1)>0:
            slopeUnc = fitline.GetParError(1)/fitline.GetParameter(1)

        if slopeUnc > 0.05:
            slopeUnc = 0.0499
        if slopeUnc > 0.02:
            if verbose:
                print 'Bad Fit Result'
                print fitline.GetName()
                print "slope Uncertainty of", slopeUnc
            fName = fitline.GetName().split('/')[-1]
            channelNum = int(fName.split('_')[2])%12+1
            badfits.append(channelNum)

            
        if 'range_0' in fitline.GetName():
            range0Unc.Fill(slopeUnc)
        if 'range_1' in fitline.GetName():
            range1Unc.Fill(slopeUnc)
        if 'range_2' in fitline.GetName():
            range2Unc.Fill(slopeUnc)
        if 'range_3' in fitline.GetName():
            range3Unc.Fill(slopeUnc)

    
    _file.cd("SummaryPlots")
    range0Unc.Write()
    range1Unc.Write()
    range2Unc.Write()
    range3Unc.Write()
    _file.Close()
    return badfits
