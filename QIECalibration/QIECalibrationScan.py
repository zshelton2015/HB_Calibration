#!/usr/bin/env python
from glob import glob
from argparse import ArgumentParser
from textwrap import dedent
from datetime import datetime
from os import system, popen, getcwd, path
from mapLinks import mapLinks
from ast import literal_eval
import sys

def qieScan(outDir, linkMask = 0, serialNum = 1, uHTR = 1, pointF = "full_hb_scan_test.txt"):
    startCommands = dedent("""\
                    test
                    qie
                    CMS
                    %s
                    %d 
                    300
                    %s
                    quit
                    exit""" % (serialNum, linkMask, pointF))                                                                                    
    with open("uHTRcommands.txt","w") as f:
        f.write(startCommands)

    if outDir[-1] != "/": outDir += "/"
    # Create output directory (if it doesn't exist) 
    system("mkdir -p %s" % outDir)
    print "About to take histo run" 
    # Take histo run
    #popen("source %s/setenv.sh; uHTRtool.exe 192.168.41.%d < uHTRcommands.txt" % (getcwd(), uHTR*4)).read()
    system("source %s/setenv.sh; uHTRtool.exe 192.168.41.%d < uHTRcommands.txt" % (getcwd(), uHTR*4))

    system("mv QIECalibration_%s.root %s" % (serialNum, outDir))


if __name__ == "__main__":
    parser = ArgumentParser("QIE Calibration Scan")
    parser.add_argument('-d', dest="topDir", default="data", help="top level directory to store qie scan data and fits")
    parser.add_argument('-c', '--cardLayout', default="cardLayout.txt", help="text file specifying teststand layout")
    #parser.add_argument('--noscan', action = "store_true", help = "process existing scan"
    parser.add_argument('--fit', action="store_true", help="run fits after qie scan")
    parser.add_argument('--saveGraphs', action="store_true", help="save graphs from fits")
    parser.add_argument('--skipShunts', action="store_true", help="skip shunts from fits")
    args = parser.parse_args()

    if not path.exists(args.cardLayout):
        print "Cannot find card layout file %s!" % args.cardLayout
        sys.exit()


    with open(args.cardLayout, "r") as f:
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
    #print "RBX =", RBX
    #print "uHTR =", uHTR
    #print "QI_SlotToBoard = %s\n" % QI_SlotToBoard

    today = datetime.now().strftime("%m-%d-%Y")

    # Will create directory if it doesn't exist, nothing otherwise
    system("mkdir -p %s/%s" % (args.topDir, today))

    dataDir = "%s/%s" % (args.topDir, today)

    # Run number to create
    run = len(glob("%s/*" % dataDir)) + 1

    # Create run directory
    runDir = "%s/Run_%d/" % (dataDir, run)
    system("mkdir -p %s" % runDir)

    # Map links
    histoMap = mapLinks(outF = runDir + "histoMap.txt", configFile = args.cardLayout, tmpDir = runDir + "tmpLinkMap")
    
    if len(histoMap) == 0:
        # Mapping failed. Terminate scan.
        print "Failed to map all links. Terminating."
        sys.exit()

    # Find active links
    activeLinks = set()
    for h in histoMap.keys():
        activeLinks.add(h/8)

    # Construct bitmask for active links
    linkMask = ""
    for link in xrange(24):
        if link in activeLinks:
            linkMask = "1" + linkMask
        else:
            linkMask = "0" + linkMask

    linkMask = eval("0b%s" % linkMask)

    serialNum = datetime.now().strftime("%m%d%y") + str(run)
    if serialNum[0] == "0":
        serialNum = serialNum[1:]
    # Run QIE scan        

    pointF = "full_hb_scan_test.txt"
    if args.skipShunts:
        pointF = "noshunt_hb_scan_test.txt"
        
    qieScan(outDir = runDir, linkMask = linkMask, serialNum = serialNum, uHTR = uHTR, pointF = pointF)

    # Compute fits
    if args.fit:
        system("./RedoFit_linearized_2d.py -d %s%s%s" % (runDir, " --saveGraphs" if args.saveGraphs else "", " --shuntList [1]" if args.skipShunts else ""))
