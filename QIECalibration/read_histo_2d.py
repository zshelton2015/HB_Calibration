from pprint import pprint
from ROOT import *
gROOT.SetBatch()
#import sqlite3 as lite
from array import array
from linearADC import *

# TODO: Un-hardcode this
QIcalibParams = {}
for i in xrange(1,17):
    QIcalibParams[i] = {}
QIcalibParams[1]  = {"offset":303.324, "slope":-7.76722}
QIcalibParams[2]  = {"offset":216.492, "slope":-7.76455}
QIcalibParams[3]  = {"offset":293.976, "slope":-7.76456}
QIcalibParams[4]  = {"offset":317.09 , "slope":-7.76632}
QIcalibParams[5]  = {"offset":275.262, "slope":-7.76717}
QIcalibParams[6]  = {"offset":272.505, "slope":-7.76711}
QIcalibParams[7]  = {"offset":230.787, "slope":-7.77254}
QIcalibParams[8]  = {"offset":261.062, "slope":-7.7672}
QIcalibParams[9]  = {"offset":336.292, "slope":-7.76707}
QIcalibParams[10] = {"offset":223.713, "slope":-7.76755}
QIcalibParams[11] = {"offset":409.359, "slope":-7.77051}
QIcalibParams[12] = {"offset":198.611, "slope":-7.76668}
QIcalibParams[13] = {"offset":342.27 , "slope":-7.76316}
QIcalibParams[14] = {"offset":314.194, "slope":-7.76687}
QIcalibParams[15] = {"offset":311.753, "slope":-7.7677}
QIcalibParams[16] = {"offset":303.609, "slope":-7.76495}

# Flip front and back adapters
flipped = False 
flipAdapters = {1:16, 2:15, 3:14, 4:13, 9:8, 10:7, 11:6, 12:5, 5:12, 6:11, 7:10, 8:9, 13:4, 14:3, 15:2, 16:1}


def isMonotonic(l):
    from numpy import diff,all
    dx = diff(l)
    return all(dx >= 0.)

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

def read_histo_2d(file_in="trial.root",shuntMult = 1, linkMap={}, injectionCardMap={},histoList = range(192)):
    shuntVal = shunt_Val[shuntMult]
    result = {}
   
    # TODO: Remove once serial number is no longer part of hist name
    serialNum = int(file_in[file_in.find("_")+1 : file_in.find(".root")])
    
    tf = TFile(file_in, "READ")
    rms={}
    mean={}
    #conSlopes = lite.connect("Slopes_Offsets_Sept8.db")  
    #cursor = conSlopes.cursor()     
    #histNameScheme = tf.GetListOfKeys()[9].GetName().split('_')
    #histNameStart = histNameScheme[0]+'_'+histNameScheme[1]

#   adcDist={}
    results = {}
    chargeBins={}
    charge={}
    histo_={}
    histo_charge={}
    if shuntMult == 1:
        qieRange = range(4)
    else:
        qieRange = range(2) #change
   
    for i_qieRange in qieRange:
        #if i_qieRange == 0 and shuntMult==1:
        #    highCurrent = False
        #else:
        #    highCurrent = True
        print "Now on shunt %.1f and range %i"%(shuntMult,i_qieRange)
        
        rms[i_qieRange]={}
        mean[i_qieRange]={}
        chargeBins[i_qieRange]={}
        charge[i_qieRange]={}
        histo_[i_qieRange]={}
        histo_charge[i_qieRange]={}
        
        if shuntVal > 0 and i_qieRange==3: continue #change
        results[i_qieRange] = {}
        rangeADCoffset = i_qieRange*64.
        for ih in histoList:
            goodLink = True
            if goodLink:

                i_link = ih/8
                i_channel = ih%8
                histNum = ih

                histName = "CHARGE_f%d_c%d_r%d_s%d" % (i_link, i_channel, i_qieRange, shuntVal)
                #print histName
                try:
                    hist = tf.Get(histName).Clone()
                    if type(hist)==type(TObject()):
                        goodLink = False
                        break
                except:
                    break
                hist.SetDirectory(0)
                histBins = hist.GetNbinsX()
                channel = (ih % 16 + 1)
                
                if flipped:
                    channel = flipAdapters[channel]

                #backplane_slotNum = linkMap[i_link]['slot']
                
                #if not backplane_slotNum in injectionCardMap:
                 #    print 'backplane slot', backplane_slotNum, ' not mapped to charge injection card!!!'
                  #   sys.exit()
                #injectioncard = injectionCardMap[backplane_slotNum][0]
                #dac = injectionCardMap[backplane_slotNum][1]
                
                results[i_qieRange][histNum] = {}
                rms[i_qieRange][histNum]={}
                mean[i_qieRange][histNum]={}
                chargeBins[i_qieRange][histNum]=array('d')
                charge[i_qieRange][histNum]=array('d')
                linADCBins=array('d')
                for i in range(i_qieRange*64,(i_qieRange+1)*64):
                    linADCBins.append(linADC(i-.5)[0])
                DACBins=array('d')
                for i_bin in range(1,hist.GetNbinsX()+1):
                    hist.GetXaxis().SetRange(i_bin,i_bin)
                    DACBins.append(int(hist.GetXaxis().GetBinLowEdge(i_bin)))
                                        
                    
                    hist.GetXaxis().SetRange(i_bin,i_bin)
                    dacVal = int(hist.GetXaxis().GetBinLowEdge(i_bin))
                    

                    info = {}
                    info["link"] = i_link
                    info["channel"] = i_channel
                    info["mean"] = []
                    info["rms"] = []
                    bincontents=[]
                    for i_capID in range(4):
                        offset = 64*(i_capID)
                        hist.GetYaxis().SetRangeUser(offset, offset+63.5)

                        info["mean"].append(hist.GetMean(2)-offset+rangeADCoffset)
                        info["rms"].append(hist.GetRMS(2))
                        #info["rms"].append(max(hist.GetRMS(2), 0.01))
                    
                    # Check for problems with 0 ADC in capID 0
                    #if (info["mean"][1] - info["mean"][0]) > 2. * max(info["rms"][1:]):
                    if info["rms"][0] > 0.01*info["mean"][0] and (info["mean"][1] - info["mean"][0]) > max(info["rms"][1:]):
                        offset = QIcalibParams[i_channel+1]["offset"]
                        slope = QIcalibParams[i_channel+1]["slope"]
                        chargeq = -(dacVal*slope + offset)
                        # Retake first data point with range 1-63 instead of 0-63
                        print "Retaking range %d fib %d ch %d dac %d (charge %d)" % (i_qieRange, i_link, i_channel, dacVal, chargeq)
                        print "Old:"
                        print info["mean"]
                        print info["rms"]

                        hist.GetYaxis().SetRangeUser(1., 63.5)
                        info["mean"][0] = hist.GetMean(2) + rangeADCoffset
                        info["rms"][0] = hist.GetRMS(2)
                        print "\nNew"
                        print info["mean"]
                        print info["rms"]
                        print "\n\n"

                    results[i_qieRange][histNum][dacVal] = info
                    
                    #pprint(results[i_qieRange][histNum][dacVal])
                         
                charge_=[]
                #query = ( injectioncard, int(dac), channel, int(highCurrent), dacvalue, dacvalue)
                #                       print injectioncard, int(dac), channel, int(highCurrent), dacvalue, dacvalue
                #cursor.execute('SELECT offset, slope FROM CARDCAL WHERE card=? AND dac=? AND channel=? AND highcurrent=? AND rangelow<=? AND rangehigh>=?', query )
                #result_t = cursor.fetchone()

                # TODO: Replace with lookup for calibration slopes/offsets
                #offset = result_t[0]
                #slope = result_t[1]
                #offset = 10.9
                #slope = -0.305
                
                offset = QIcalibParams[channel]["offset"]
                slope = QIcalibParams[channel]["slope"]

                
                
                for dacvalue in DACBins:
                #    if dacvalue > 48000: continue
                    
                    # Already converted to charge
                    #current = dacvalue*slope + offset
                    #chargeq = current*25e6
                    chargeq = dacvalue*slope + offset
                    chargeBins[i_qieRange][histNum].append(-1.*chargeq)
                
                histo_charge[i_qieRange][histNum]={}
                for i_capID in range(4)[::-1]:
                    
                    histo_charge[i_qieRange][histNum][i_capID]=TH2F("histocharge_fC_%i_%i_qieRange_%i_shunt_%i_%i_capID_%i"%(ih, channel,i_qieRange,int(shuntMult),int(shuntMult%1*10),i_capID),"histocharge_fC_%i_%i_range_%i_shunt_%i_%i_capID_%i"%(ih, channel,i_qieRange,int(shuntMult),int(shuntMult%1*10),i_capID),len(chargeBins[i_qieRange][histNum])-1,chargeBins[i_qieRange][histNum], len(linADCBins)-1, linADCBins)
                    
                    histo_charge[i_qieRange][histNum][i_capID].SetDirectory(0)
                    
                    for ix in range(1,hist.GetNbinsX()+1):
                        for iy in range(1,64):
                            histo_charge[i_qieRange][histNum][i_capID].SetBinContent(ix,iy,hist.GetBinContent(ix,iy+i_capID*64))
                    rms[i_qieRange][histNum][i_capID]=array('d')
                    mean[i_qieRange][histNum][i_capID]=array('d')
                    for ix in range(1,hist.GetNbinsX()+1):  
                        charge[i_qieRange][histNum].append(float(chargeBins[i_qieRange][histNum][ix-1]))
                        adcDist = histo_charge[i_qieRange][histNum][i_capID].ProjectionY("adc_%i_%i_qieRange_%i_shunt_%i_%i_capID_%i"%(ih, channel,i_qieRange,int(shuntMult),int(shuntMult%1*10),i_capID),ix,ix)
                        N = adcDist.Integral()
                        if N==0:continue
                        
                        # If there are excess events in bin 1, ignore them
                        #if adcDist.GetBinContent(1) > 0. and adcDist.GetRMS() - mean[i_qieRange][histNum][i_capID][-1] < 0:
                        #if histo_charge[i_qieRange][histNum][i_capID].GetBinContent(ix,1) > 10. and histo_charge[i_qieRange][histNum][i_capID].GetBinContent(ix-1,1) < 0.1: 
                        if i_capID == 0 and histo_charge[i_qieRange][histNum][0].GetBinContent(ix,1) > 10. and histo_charge[i_qieRange][histNum][1].GetBinContent(ix,1) < 0.1:
                            print "Retaking data for range %d fib %d ch %d capID %d charge %d" % (i_qieRange, i_link, i_channel, i_capID, histo_charge[i_qieRange][histNum][i_capID].GetXaxis().GetBinCenter(ix))
                            print "Old:", adcDist.GetMean()
                            adcDist.GetXaxis().SetRange(2,adcDist.GetNbinsX())    
                            print "New:", adcDist.GetMean()
                        
                        mean[i_qieRange][histNum][i_capID].append(adcDist.GetMean())
                        rms[i_qieRange][histNum][i_capID].append(max(adcDist.GetRMS(),0.25)/N**0.5)
                        

                if not goodLink: continue
        #print histo_charge                                        
    
    tf.Close()
    return results, mean, rms, charge
    #return results, mean, rms, charge, histo_charge
