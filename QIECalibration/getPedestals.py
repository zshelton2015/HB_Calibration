from ROOT import *
from linearADC import *
import os
from array import array

# Fixes seg fault from importing Quiet
try:
    Quiet(TObject())
except NameError:
    from utils import Quiet

bin0startLevel = -0.5

# def CleanGraph(graph, i_range):
#     vOffset = i_range*64
#     points = range(graph.GetN())
     
#     return graph


def getPedestals(graphs_shunt, shuntMult_list, histoList,dirName, date, run, verbose=False):
    pedestalVals = {}
    if verbose:
        print "graphs_shunt = ", graphs_shunt
    if not os.path.exists("%s/PedestalPlots"%dirName):
        os.mkdir("%s/PedestalPlots"%dirName)
    
    
    _file = TFile("%s/PedestalPlots/pedestalMeasurement_%s_%s.root"%(dirName,date,run),"update")

    c1 = TCanvas()
    c1.Divide(2,2)
    c2 = TCanvas('c2', 'Plots', 1000, 500)
    c2.SetFillColor(0)
    c2.SetGrid()
   
    shuntPeds = {}

    pedHists = {}
    for i_shunt in shuntMult_list:
        pedHists[i_shunt] = TH1F("pedestalCharge_%s"%str(i_shunt).replace(".","_"),"pedestalCharge_%s"%str(i_shunt).replace(".","_"),-200,-100,100)

    
    for ih in histoList:
        _file.mkdir("h%i"%ih)
        _file.cd("h%i"%ih)
        #print ih
        
        #lowCurrentPeds = []
        for i_capID in range(4):
            #remove lower and upper ends of ADC to make it clean
#            graph = CleanGraph(graphs_shunt[1.0][ih][i_capID],0)
            graph = graphs_shunt[1.0][ih][i_capID]
            graph = graphs_shunt[1.0][ih][i_capID]
            f1= TF1("f1","pol1",200,600);

            #print "pedestalFit"
            #print graph
            #print graph.GetN()
            if not verbose:
                graph.Fit("f1","R0Q")
            else:
                graph.Fit("f1","R0")
            line = graph.GetFunction("f1")
            graph.Write()
            #pedestal is the x-intercept of the graph (-offset/slope)
            #lowCurrentPeds.append(-1*(line.GetParameter(0)-bin0startLevel)/line.GetParameter(1))


        #get high current peds
        highCurrentPeds = []
        highCurrentShuntPeds = {}
        for i_shunt in shuntMult_list:
#            if i_shunt==1:
#                continue
            highCurrentShuntPeds[i_shunt]=[]
            for i_capID in range(4):
                #print ih, i_shunt, i_capID
                # graph = CleanGraph(graphs_shunt[i_shunt][ih][i_capID],0)
                graph = graphs_shunt[i_shunt][ih][i_capID]
                #print graph, i_shunt
                #print graph.GetN()
            #   if i_shunt==1.5 and ih==14 and i_capID==1:
            #       graph.Draw("ap")
            #       c2.SaveAs("trial_2.pdf")        
                if not verbose:
                    graph.Fit("pol1","0Q")
                else:    
                    graph.Fit("pol1","0")
                line = graph.GetFunction("pol1")
                graph.Write()
                if not line.GetParameter(1)==0.:
                    highCurrentShuntPeds[i_shunt].append(-1*(line.GetParameter(0)-bin0startLevel)/line.GetParameter(1))                    
                else:
                    highCurrentShuntPeds[i_shunt].append(-999.)
                if highCurrentShuntPeds[i_shunt]>100:
                    pedHists[i_shunt].Fill(99.5)
                elif highCurrentShuntPeds[i_shunt]<-100:
                    pedHists[i_shunt].Fill(-99.5)
                else:
                    pedHists[i_shunt].Fill(highCurrentShuntPeds[i_shunt])

        # Removed by Danny, June 21 2018, I don't think this is needed any more, but if the pedestal parts stop working, try uncommenting the block below

        # #make graphs of the shunt vs measured pedestal
        # graphs = []
        # for i_capID in range(4):
        #     x = shuntMult_list[1:]
        #     y = []
        #     for s in shuntMult_list[1:]:
        #         y.append(highCurrentShuntPeds[s][i_capID])
        #     #print x
        #     #print y
        #     _x = array('d',x)
        #     _y = array('d',y)

        #     graphs.append(TGraph(len(x),_x,_y))
        #     graphs[-1].SetNameTitle(graphs_shunt[1.0][ih][i_capID].GetTitle().replace("_shunt_1_0_","_"),graphs_shunt[1.0][ih][i_capID].GetTitle().replace("_shunt_1_0_","_"))
        #     graphs[-1].GetYaxis().SetRangeUser(-500,150)
        #     if not verbose:
        #         graphs[-1].Fit("pol1","0Q")
        #     else:
        #         graphs[-1].Fit("pol1","0")
        #     line = graphs[-1].GetFunction("pol1")
        #     c1.cd(i_capID+1)
        #     graphs[-1].SetMarkerStyle(7)
        #     graphs[-1].SetMarkerSize(2)
        #     graphs[-1].GetXaxis().SetTitle("Shunt Value (nominal)")
        #     graphs[-1].GetYaxis().SetTitle("Measured total pedestal")
        #     graphs[-1].Draw("ap")
        #     graphs[-1].Write()
        #     highCurrentPeds.append(line.Eval(1))
            



        #c1.SaveAs("%s/PedestalPlots/%s.pdf"%(dirName,graphs_shunt[1.0][ih][0].GetTitle().replace("_shunt_1_0_capID_0","")))
        # if verbose:
        #     c1.SaveAs("%s/PedestalPlots/%s.pdf"%(dirName,graphs_shunt[1.0][ih][0].GetTitle().replace("_shunt_1_0_capID_0","")))
        # else:
        #     Quiet(c1.SaveAs)("%s/PedestalPlots/%s.pdf"%(dirName,graphs_shunt[1.0][ih][0].GetTitle().replace("_shunt_1_0_capID_0","")))
        
        pedestalVals[ih] = {#"low":lowCurrentPeds,
                            #"high":highCurrentPeds,
                            "shunts":highCurrentShuntPeds,
                            }


        
    for i_shunt in shuntMult_list:
        pedHists[i_shunt].Write()
    _file.Close()

    return pedestalVals
