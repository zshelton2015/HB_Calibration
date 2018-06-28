#!/usr/bin/env python
from os import system,popen
from textwrap import dedent
import sys
from time import sleep
import os
from DAC import setDAC_multi
import time		  
from argparse import ArgumentParser
from sendCommands import send_commands
import re
from pprint import pprint
from ast import literal_eval    # Safe eval
from ROOT import *
# 0x : value must start with literal '0x'
# [A-Fa-f0-0] : only values of A-F, a-f, or 0-9 allowed
# + : multiple numbers allowed
hexfind = re.compile(r"0x[A-Fa-f0-9]+")

#RBX = "HB1"
#uHTR = 1
#QI_SlotToBoard = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8}


#injectorBoardToQIECard = {}
#injectorBoardToQIECard[1] = {"RM":4, "Slot":1}

#uHTRToQIECard = {}
#uHTRToQIECard[0] = {"RM":4, "Slot":1, "Igloo":"Top"}
#uHTRToQIECard[1] = {"RM":4, "Slot":1, "Igloo":"Bot"}

def histoRun(outF, uHTR = 1):
    startCommands = dedent("""\
                    link
                    histo
                    integrate
                    50
                    0
                    %s
                    0
                    quit
                    quit
                    exit""" % (outF))
    with open("uHTRcommands.txt","w") as f:
        f.write(startCommands)
    
    # Create output directory (if it doesn't exist) 
    os.system("mkdir -p %s" % os.path.dirname(outF))
    
    # Take histo run
    popen("uHTRtool.exe 192.168.41.%d < uHTRcommands.txt" % (uHTR*4)).read()
    

def mapLinks(outF = "", configFile = "cardLayout.txt", tmpDir = ".tmpMap"):
    with open(configFile, "r") as f:
        for i,line in enumerate(f):
            if line[0] == "#":
                # Skip comments
                continue

            line = line.strip() 
            if i == 1:
                RBX = str(line)
            elif i == 2:
                uHTR = int(line)
            elif i == 3:
                QI_SlotToBoard = dict(literal_eval(line))
   
    print "RBX =", RBX
    print "uHTR =", uHTR
    print "QI_SlotToBoard = %s\n" % QI_SlotToBoard

    # Map histogram number to: QIESlot, Top/Bot, UID, QI slot, QI board, QI channel
    histoMap = {}
    
    # Step 1: Map uHTR fiber to Igloo
    print "Mapping uHTR links to QIE Igloos"
    setDAC_multi(40000)
    print "" 
    # Turn on fixed range mode and set all to range 0
    #fixRangeCmds = ["put %s-[1-4]-QIE[1-64]_FixRange 256*0" % RBX, \
     #               "put %s-[1-4]-QIE[1-64]_RangeSet 256*0" % RBX]
    #send_commands(cmds = fixRangeCmds)

    # Set ranges for each QIE card
    # Top igloo (QIE 1-8 ): range 1    (should read 127)
    # Bot igloo (QIE 9-16): range 2    (should read 191)
    for rm in xrange(1,5):
        for slot in xrange(1,5):
            print "Now on rm %d slot %d" % (rm,slot)
            resetRangeCmds = []
            send_commands(cmds = resetRangeCmds)
            sleep(0.5) 
            iglooRangeCmds = ["get %s-%d-%d-UniqueID" % (RBX, rm, slot), \
                              "put %s-[1-4]-QIE[1-64]_FixRange 256*0" % RBX, \
                              "put %s-[1-4]-QIE[1-64]_RangeSet 256*0" % RBX, \
                              "put %s-%d-QIE[%d-%d]_FixRange 16*1" % (RBX, rm, (slot-1)*16 + 1, slot*16), \
                              "put %s-%d-QIE[%d-%d]_RangeSet 8*1" % (RBX, rm, (slot-1)*16 + 1, slot*16 - 8), \
                              "put %s-%d-QIE[%d-%d]_RangeSet 8*2" % (RBX, rm, slot*16 - 7, slot*16), \
                              "get %s-%d-QIE[%d-%d]_FixRange" % (RBX, rm, (slot-1)*16 + 1, slot*16), \
                              "get %s-%d-QIE[%d-%d]_RangeSet" % (RBX, rm, (slot-1)*16 + 1, slot*16)]
            ngccm_output = send_commands(cmds = iglooRangeCmds)
            if ngccm_output[0]["result"].find("ERROR") >= 0:
                # Card not found, continue
                print "Card not found in rm %d slot %d!" % (rm,slot)
                continue
            # Find two UniqueID hex values
            uidhex = hexfind.findall(ngccm_output[0]["result"])
            if len(uidhex) == 2:
                UniqueID = "%s_%s" % (uidhex[0], uidhex[1])
                print "Card found with UniqueID: ", UniqueID
            elif len(uidhex) == 1:
                # First value of unique ID is 0
                UniqueID = "0_%s" % uidhex[0]
                print "Card found with UniqueID: ", UniqueID
            else:
                print "Error reading UniqueID for RM %d Slot %d:" % (rm,slot), uidhex
                UniqueID = ""
            print "" 
            
            # Take histo run
            histoRun("%s/uHTRToIgloo/rm_%d_slot_%d.root" % (tmpDir, rm, slot), uHTR)

            # Load histo run file
            f = TFile.Open("%s/uHTRToIgloo/rm_%d_slot_%d.root" % (tmpDir, rm, slot), "read")
            for h in xrange(0,192,8):
                hist = f.Get("h%d" % h)
                mean = hist.GetMean()
                rms = hist.GetRMS()
                integral = hist.Integral()
                if mean > 100 and mean < 150 and rms < 1 and integral > 100:
                    # Found Top igloo
                    if h not in histoMap.keys():
                        for h_i in xrange(h, h+8):
                            histoMap[h_i] = {"RM":rm, "Slot":slot, "Igloo":"Top", "UniqueID":UniqueID, "Link":(h_i/8)}
                    else:
                        print "h%d already in the histoMap!" % h

                        
                elif mean > 150 and mean < 200 and rms < 1 and integral > 100:
                    # Found Bot igloo
                    if h not in histoMap.keys():
                        for h_i in xrange(h, h+8):
                            histoMap[h_i] = {"RM":rm, "Slot":slot, "Igloo":"Bot", "UniqueID":UniqueID, "Link":(h_i/8)}
                    else:
                        print "h%d already in the histoMap!" % h
                    
            f.Close()

    # Turn off fixed range mode and set all to range 0
    fixRangeCmds = ["put %s-[1-4]-QIE[1-64]_FixRange 256*0" % RBX, \
                    "put %s-[1-4]-QIE[1-64]_RangeSet 256*0" % RBX]
    send_commands(cmds = fixRangeCmds)


    
    # Step 2: Map QI board to QIE card
    print "\nMapping QI boards to QIE cards"
    #for QIslot in xrange(1,9):
    for QIslot in sorted(QI_SlotToBoard.keys()): 
        # Turn on QI board in slot QIslot and inject in all channels
        setDAC_multi(10000, "%s" % QIslot)
        
        # Take histo run
        histoRun("%s/QIslotToQIEcard/QIslot_%d.root" % (tmpDir, QIslot), uHTR)

        # Parse histo file
        f = TFile.Open("%s/QIslotToQIEcard/QIslot_%d.root" % (tmpDir, QIslot))
        for h in xrange(0,192,8):
            hist = f.Get("h%d" % h)
            if hist.GetMean() > 50 and hist.GetRMS() < 2 and hist.Integral() > 100:
                # Found QIE card
                if h not in histoMap.keys():
                    print "Could not find h%d in the map. Check uHTR link step!" % h

                for h_i in xrange(h, h+8):
                    if h_i in histoMap.keys():
                        histoMap[h_i]["QIslot"] = QIslot
                        try:
                            histoMap[h_i]["QIboard"] = QI_SlotToBoard[QIslot]
                        except KeyError:
                            print "Could not find a QI board number for QI slot %d. Check configuration file!" % QIslot
                    else:
                        print "Can't find h%d in histoMap!" % h_i
        f.Close()
    
    # Step 3: Map QI channel to QIE channel
    print "\nMapping QI channels to QIE channels"
    
    # Only need to loop over odd channels
    for QIchannel in xrange(1,17):
        # Turn on channel QIchannel for all boards
        setDAC_multi("%d:10000" % QIchannel)

        # Take histo run
        histoRun("%s/QIchannelTOQIEchannel/QIchannel_%d.root" % (tmpDir, QIchannel), uHTR)

        # Parse histo run
        f = TFile.Open("%s/QIchannelTOQIEchannel/QIchannel_%d.root" % (tmpDir, QIchannel))
        for h in xrange(0,192):
            hist = f.Get("h%d" % h)
            if hist.GetMean() > 50 and hist.GetRMS() < 2 and hist.Integral() > 100:
                # Found QIE channel

                histoMap[h]["QIchannel"] = QIchannel
                histoMap[h]["QIE"] = h % 8 + 8 * (1 if histoMap[h]["Igloo"] == "Bot" else 0) + 1 
                #histoMap[h+1]["QIchannel"] = QIchannel + 1
                #histoMap[h+1]["QIE"] = (h+1) % 8 + 8 * (1 if histoMap[h+1]["Igloo"] == "Bot" else 0) + 1 
        
        f.Close()

    # Check mapping and flag problem slots
    problemSlots = []
    for h in sorted(histoMap.keys()):
        try:
            histoMap[h]["QIslot"]
            histoMap[h]["QIboard"]
            histoMap[h]["QIchannel"]
            histoMap[h]["QIE"]
        except KeyError:
            rm = histoMap[h]["RM"]
            slot = histoMap[h]["Slot"]
            if (rm,slot) not in problemSlots:
                print "Error mapping card in RM %d Slot %d" % (rm,slot)
                problemSlots.append( (rm,slot) )

    if len(problemSlots) > 0:
        return {}

    pprint(histoMap)
    setDAC_multi(0)
    #os.system("rm -rf %s" % tmpDir)

    if outF != "":
        if not os.path.exists(os.path.dirname(outF)):
            os.system("mkdir -p %s" % os.path.dirname(outF))

        with open(outF, "w+") as f:
            f.write("# QIE channels numbered 1-16, uHTR links numbered 0-23\n")
            f.write("%s" % histoMap)


    return histoMap

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--dir", dest="outDir", default="histoMap", help="output directory" )
    args = parser.parse_args()

    if args.outDir[-1] == "/": args.outDir = args.outDir[:-1]

    histoMap = mapLinks()
    os.system("mkdir -p %s" % args.outDir)
    
    with open("%s/histoMap.txt" % args.outDir, "w+") as f:
        f.write("# QIE channels numbered 1-16, uHTR links numbered 0-23\n")
        f.write("%s" % histoMap)
    

