from ROOT import *
import sys
import numpy
from array import array
import os
from linearADC import *

try:
    Quiet(TObject())
except NameError:
    from utils import Quiet 


####Change the fit to return slopes/offsets in terms of range 0 values for all ranges

#gROOT.SetBatch(kTRUE)
#ROOT.gStyle.SetCanvasColor(kWhite)
#gStyle.SetStatStyle(kWhite)
#gStyle.SetTitleStyle(kWhite)

graphOffset = [100,500,3000,8000]
saveResiduals = True

startVal = [[3.2,-15],
            [3.2,-20],
            [3.2,-20],
            [3.2,-20]]


Varlimits = [[[2.5,4.0],[-50,100]],
             [[2.5,4.0],[-50,1000]],
             [[2.5,4.0],[-500,1000]],
             [[2.5,4.0],[-5000,10000]]]



lineColors = [kRed, kBlue, kGreen+2, kCyan] 
shunt_Val ={1:0,
            1.5:1,
            2:2,
            3:4,
            4:8,
            5:16,
            6:18,
            7:20,
            8:24,
            9:26,
            10:28,
            11:30,
            11.5:31}




shuntMultList = shunt_Val.keys()
shuntMultList.sort()


def doFit_combined(graphList, saveGraph = False, qieNumber = 0, qieBarcode = "", qieUniqueID = "", useCalibrationMode = True, outputDir = '', shuntMult = 1, pedestalVals = {"low":[0,0,0,0],"high":[0,0,0,0],"shunt":{}}, verbose=False):

    fitLines =  []
    slopes =  []
    offsets =  []
    maxResiduals = []
#        pedestal = [0]*4
    linearizedGraphList =  []

    #print graphList

    outputTGraphs = TFile(outputDir.replace("outputPlots","")+"fitResults_%s.root"%qieUniqueID,"update")

    saveName = None


    if shuntMult == 1: 
        ranges = range(4)
    else :
        ranges = range(2) #change
    
    for i_range in ranges:
        #choose the pedestal to subtract according to the whether it is low current or high current
        #if i_range == 0 and shuntMult==1:
        #    pedestal = pedestalVals["low"]
        #elif  shuntMult==1:

        #######################################################
        #if shuntMult == 1:
        #    pedestal = pedestalVals["high"]
        #else:
        #    pedestal = pedestalVals["shunts"][shuntMult]
        #######################################################
        pedestal = pedestalVals["shunts"][shuntMult]


        vOffset = i_range*64
        graphs = graphList[i_range]
        if graphs==None: 
            fitLines.append(None)
            continue
        else:                   
            fitLines.append([])
            maxResiduals.append([])


#       if pedestal==None:
#           pedestal = []

        for i_capID in range(4):
            #print i_graph
            nominalgraph =  graphs[i_capID]
            #print nominalgraph.GetName()
            # if shuntMult == 1:
            #     outputTGraphs.cd("adcVsCharge")
            # else:
            #     outputTGraphs.cd("Shunted_adcVsCharge")
            # nominalgraph.Write()
            graph = nominalgraph.Clone("%s_linearized"%nominalgraph.GetName())
            graph.SetNameTitle("%s_linearized"%nominalgraph.GetName(),"%s_linearized"%nominalgraph.GetName())

            points = range(graph.GetN())
            points.reverse()
            maxCharge = -9e9
            minCharge = 9e9
            for p in points:
                x = graph.GetX()[p]-vOffset
                # nominalgraph.GetX()[p] -= pedestal[i_capID]
                graph.GetX()[p] -= pedestal[i_capID]


            graph.GetXaxis().SetTitle("Charge (fC)")
            graph.GetYaxis().SetTitle("Linearized ADC")

            outputTGraphs.cd("LinadcVsCharge")
            # if shuntMult == 1: 
            # else:
            #     outputTGraphs.cd("Shunted_LinadcVsCharge")
            
            if verbose:
                print "Pedestals Used"
                print pedestal

            if graph.GetN() > 1:
                if verbose:
                    print "TOTAL:",graph.GetN()
                f1= TF1("f1","pol1",200,600);
#               f1.FixParameter(0,-0.5)
                #if (i_range==0 and shuntMult==1):
                #    graph.Fit("f1","R0") 
                #else:
                #    graph.Fit("pol1","0") 
                if not verbose:
                    graph.Fit("pol1","0Q")               
                else: 
                    graph.Fit("pol1","0")               
                linearizedGraphList.append(graph) 
                
                #if (i_range==0 and shuntMult==1):
                #   fitLine = graph.GetFunction("f1")
                #else:                               
                #   fitLine = graph.GetFunction("pol1")
                fitLine =  graph.GetFunction("pol1")
                fitLine.SetNameTitle("fit_%s"%graph.GetName(),"fit_%s"%graph.GetName())
                fitLines[-1].append(fitLine)
            else:
                linearizedGraphList.append(graph)
                fitLine = TF1("fit_%s"%graph.GetName(),"pol1",-999,999)
                fitLine.SetParameter(0,0)
                fitLine.SetParameter(1,0)
                fitLine.SetParError(0,999)
                fitLine.SetParError(1,999)
                fitLine.SetNameTitle("fit_%s"%graph.GetName(),"fit_%s"%graph.GetName())
                fitLines[-1].append(fitLine)
                print 'PROBLEM'
                print graph.GetName()
                continue
            graph.Write()

            if saveGraph or saveResiduals:
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

                absResidual = []
                for i in range(N):
                    absResidual.append((yVals[i]-fitLine.Eval(xVals[i])))
                    residuals.append((yVals[i]-fitLine.Eval(xVals[i]))/max(yVals[i],0.001))
                    xLow = (xVals[i]-exVals[i])
                    xHigh = (xVals[i]+exVals[i])
                    residualErrors.append((eyVals[i]/max(yVals[i],0.001)))
                    x.append(xVals[i])
                maxResidual = max(absResidual, key=abs)
                maxResiduals[-1].append(abs(maxResidual))

                                
            if saveGraph:
                qieInfo = ""

                saveName = outputDir
                if saveName[-1]!='/':
                    saveName += '/'
                saveName += "plots/"
               
                if qieBarcode != "":
                    qieInfo += ", Barcode " + qieBarcode
                
                if qieUniqueID != "": 
                    qieInfo += "  UID "+qieUniqueID
                else:
                    qieUniqueID = "UnknownID"
                
                saveName += qieUniqueID
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
                saveName += ".pdf"
                graph.SetTitle("LinADC vs Charge, Range %i Shunt %s%s" % (i_range,str(shuntMult).replace(".","_"),qieInfo))
                graph.GetYaxis().SetTitle("Lin ADC")
                graph.GetYaxis().SetTitleOffset(1.2)
                graph.GetXaxis().SetTitle("Charge fC")


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
            #   p2.SetTopMargin(0)
            #   p2.SetBottomMargin(0.3)
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
                text.AddText("Slope =  %.4f +- %.4f LinADC/fC" % (fitLine.GetParameter(1), fitLine.GetParError(1)))
                text.AddText("Offset =  %.2f +- %.2f LinADC" % (fitLine.GetParameter(0), fitLine.GetParError(0)))
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
                if minCharge < 10: minCharge = -10
                
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

    if shuntMult == 1:
        ranges = range(4)
    else:
        ranges = range(2)  #change       
    params = [[],[],[],[]]
    unshunted_params = [[],[],[],[]]    

    for irange in ranges:
        if fitLines[irange]==None:
            for icapID in range(4):
                params[irange].append([-1,-1])
                continue
        for icapID in range(4):
#           if shuntMult==1:
#               high_range[irange].append([fitLines[0][icapID].GetParameter(1),fitLines[0][icapID].GetParameter(0),fitLines[0][icapID].GetParError(1)])

            ####################################################################
            #if irange==0 and shuntMult==1:
            #    offset = -0.5
            #else:
            #    offset = fitLines[irange][icapID].GetParameter(0)
            ####################################################################
            offset = fitLines[irange][icapID].GetParameter(0)
            
            
            slope = fitLines[irange][icapID].GetParameter(1)
            uncertainty = fitLines[irange][icapID].GetParError(1)

            params[irange].append([slope,offset,uncertainty,maxResiduals[irange][icapID]])
            if shuntMult==1:
                unshunted_params[irange].append([slope,offset,uncertainty,maxResiduals[irange][icapID]])
                
        
       # print  high_range
    #sys.exit()
        # outputTGraphs.cd("LinadcVsCharge")
        # for graph in linearizedGraphList:
        #       graph.Write()

    outputTGraphs.cd("fitLines")
    if shuntMult==1:
        ranges = range(4)
    else:
#        outputTGraphs.cd("Shunted_fitLines")
        ranges = range(3) #change
    for i_range in ranges:
        if graphList[i_range]==None: continue
#           print 'Writing'
        for fitLine in fitLines[i_range]:
            fitLine.SetNpx(1000)
            fitLine.Write()

        if saveGraph:
            if saveName==None: continue
            saveName = saveName.replace("_capID"+str(i_capID),"")
            c1 = TCanvas()
            slopes = []
            offsets = []
            for i_capID in range(4):
                graph = graphList[i_range][i_capID]
                fitLine = fitLines[i_range][i_capID]
                #            graph.SetMarkerStyle(20+i_capID)
                fitLine.SetLineColor(lineColors[i_capID])
                fitLine.SetLineWidth(2)

                slopes.append( (fitLine.GetParameter(0), fitLine.GetParError(0) ) )
                offsets.append( (fitLine.GetParameter(1), fitLine.GetParError(1) ) )
                if i_capID==0:
                    graph.Draw("ap")
                    if shuntMult == -1:
                        graph.SetTitle("LinADC vs Charge, Range %i, %s, QIE %.1f" % (i_range,qieUniqueID,qieNumber))
                    else:
                        graph.SetTitle("LinADC vs Charge, Range %i, %s, QIE %i,Shunt %.1f" % (i_range,qieUniqueID,qieNumber,shuntMult))
                    graph.GetYaxis().SetRangeUser(ymin-graphOffset[i_range],graph.GetYaxis().GetXmax()+graphOffset[i_range]*4)
                else:
                    N_ = graph.GetN()
                    x_ = graph.GetX()
                    y_ = graph.GetY()
                    for n in range(N_):
                        graph.SetPoint(n,x_[n],y_[n]+(graphOffset[i_range]*i_capID))
                        fitLine.SetParameter(1,fitLine.GetParameter(1)+(graphOffset[i_range]*i_capID))
                    graph.Draw("p, same")
                    fitLine.Draw("same")
                    if not i_range==3:
                        text = TPaveText(xmin +5, ymax + 3*graphOffset[i_range] - (ymax-ymin)*(.7) ,xmin + 50 ,ymax+3.75*graphOffset[i_range])
                    else:
                        text = TPaveText(xmin +25, ymax + 2*graphOffset[i_range] - (ymax-ymin)*(.7) ,xmin + 75 ,ymax+3.75*graphOffset[i_range])

            text.SetFillColor(kWhite)
            text.SetFillStyle(4000)
            text.SetTextAlign(11)
            text.AddText("CapID 0:")
            text.AddText("    Slope =  %.2f +- %.8f fC/ADC" % slopes[0])
            text.AddText("    Offset =  %.2f +- %.8f fC" % offsets[0])
            text.AddText("CapID 1:")
            text.AddText("    Slope =  %.2f +- %.2f fC/ADC" % slopes[1])
            text.AddText("    Offset =  %.2f +- %.2f fC" % offsets[1])
            text.AddText("CapID 2:")
            text.AddText("    Slope =  %.2f +- %.2f fC/ADC" % slopes[2])
            text.AddText("    Offset =  %.2f +- %.2f fC" % offsets[2])
            text.AddText("CapID 3:")
            text.AddText("    Slope =  %.2f +- %.2f fC/ADC" % slopes[3])
            text.AddText("    Offset =  %.2f +- %.2f fC" % offsets[3])
            text.Draw("same")
            
            if not verbose:
                Quiet(c1.SaveAs)(saveName)
            else:
                c1.SaveAs(saveName)
            #c1.SaveAs(saveName)
                
            # directory = saveName.split("Lin")[0]
            # os.system("gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=%s/Plots_range_%i_shunt_%s.pdf %s/LinADCvsfC_qie*_range%i_capID*_shunt_%s_NotCalMode.pdf"%(directory,i_range, str(shuntMult).replace(".","_"),directory,i_range, str(shuntMult).replace(".","_")))

    return params, unshunted_params
