from ROOT import *
import sqlite3
from array import array
gROOT.SetBatch(kTRUE)
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

def graphParamDist(paramFileName):

    outputDirectory = paramFileName.split('qieCalibrationParam')[0]
    #outputDirectory = '/Users/titasroy/cmshcal11_github/Data/database_05_22/'
    #paramDB = sqlite3.connect(paramFileName)
    #cursor = paramDB.cursor()
    #qieCards = [x[0] for x in list(set(cursor.execute("select id from qieshuntparams").fetchall()))]
    #print qieCards
    qieCards = []
    #for uniqueID in qieCards:
    #    print uniqueID
    hists = {}
    
    slopes_ = {}
       
    #parameterValues = cursor.execute("select * from qieshuntparams where id = ?", [str(uniqueID)]).fetchall()
    for shuntMult in shuntMultList:
        slopes_[shuntMult]={}
        slopes_[shuntMult][0] = {0:array('d'),
                  1:array('d'),
                  2:array('d'),
                  3:array('d'),} 
        slopes_[shuntMult][1] = {0:array('d'),
                                  1:array('d'),
                                  2:array('d'),
                                  3:array('d'),} 
        slopes_[shuntMult][2] = {0:array('d'),
                                  1:array('d'),
                                  2:array('d'),
                                  3:array('d'),} 
     
        slopes_[shuntMult][3] = {0:array('d'),
                                  1:array('d'),
                                  2:array('d'),
                                  3:array('d'),} 
        #range0MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset), min(uncertainty), max(uncertainty) from qieshuntparams where id = ? and range=? and shunt=?", [str(uniqueID),0,shuntMult]).fetchone()
        #range1MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset), min(uncertainty), max(uncertainty) from qieshuntparams where id = ? and range=? and shunt=?", [str(uniqueID),1,shuntMult]).fetchone()
        #range2MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset), min(uncertainty), max(uncertainty) from qieshuntparams where id = ? and range=? and shunt=?", [str(uniqueID),2,shuntMult]).fetchone()
        #range3MinMax = cursor.execute("select min(slope), max(slope), min(offset), max(offset), min(uncertainty), max(uncertainty) from qieshuntparams where id = ? and range=? and shunt=?", [str(uniqueID),3,shuntMult]).fetchone()

           # if shuntMult>1: 
            #    range3MinMax= [1,1,1,1] 
             #   range2MinMax= [1,1,1,1] 
                #range1MinMax= [1,1,1,1]
            

        hists[shuntMult] = {0:[TH1F("Range0Slopes_shunt%.1f"%shuntMult,"Range0Slopes_shunt%.1f"%shuntMult,100,.94*.3/shuntMult,1.1*.3/shuntMult), TH1F("Range0Offsets_shunt%.1f"%shuntMult,"Range0Offsets_shunt%.1f"%shuntMult,100,-1., 0.), TH1F("Range0Uncertainties_shunt%.1f"%shuntMult,"Range0Uncertainties_shunt%.1f"%shuntMult, 50,1.*10**-8,10.*10**-6)],
                                1:[TH1F("Range1Slopes_shunt%.1f"%shuntMult,"Range1Slopes_shunt%.1f"%shuntMult,100,.94*.3/shuntMult,1.1*.3/shuntMult), TH1F("Range1Offsets_shunt%.1f"%shuntMult,"Range1Offsets_shunt%.1f"%shuntMult,100,-20,150),TH1F("Range1Uncertainties_shunt%.1f"%shuntMult,"Range1Uncertainties_shunt%.1f"%shuntMult, 50,1.*10**-8,10.*10**-6)],
                                2:[TH1F("Range2Slopes_shunt%.1f"%shuntMult,"Range2Slopes_shunt%.1f"%shuntMult,100,.94*.3/shuntMult,1.1*.3/shuntMult), TH1F("Range2Offsets_shunt%.1f"%shuntMult,"Range2Offsets_shunt%.1f"%shuntMult,100,-20,150), TH1F("Range2Uncertainties_shunt%.1f"%shuntMult,"Range2Uncertainties_shunt%.1f"%shuntMult, 50,1.*10**-8,10.*10**-6)],
                                3:[TH1F("Range3Slopes_shunt%.1f"%shuntMult,"Range3Slopes_shunt%.1f"%shuntMult,100,.94*.3/shuntMult,1.1*.3/shuntMult), TH1F("Range3Offsets_shunt%.1f"%shuntMult,"Range3Offsets_shunt%.1f"%shuntMult,100,-20,150), TH1F("Range3Uncertainties_shunt%.1f"%shuntMult,"Range3Uncertainties_shunt%.1f"%shuntMult, 50,1.*10**-8,10.*10**-6)],
                     }

        # TODO: Fix this
        for entry in parameterValues:
            qieID, barcode, qieNum, i_capID, qieRange,shuntMult, Gsel, slope, offset, uncertainty= entry
            slopes_[shuntMult][i_capID][qieRange].append(float(slope))         
            hists[shuntMult][qieRange][0].Fill(slope)
            hists[shuntMult][qieRange][1].Fill(offset)
            hists[shuntMult][qieRange][2].Fill(uncertainty)




        outputParamRootFile = TFile("%s/fitResults_%s.root"%(outputDirectory, uniqueID.replace(" ","_")),"update")

        outputParamRootFile.cd("SummaryPlots")

        for shuntMult in hists:
            for i_range in hists[shuntMult]:
                hists[shuntMult][i_range][0].Write()
                hists[shuntMult][i_range][1].Write()
                hists[shuntMult][i_range][2].Write()
                


if __name__=="__main__":

    import sys

    if len(sys.argv)==2:
        outFile = sys.argv[1]

#        graphParamDist(outFile)
