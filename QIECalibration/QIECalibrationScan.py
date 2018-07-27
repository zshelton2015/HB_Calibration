#!/usr/bin/env python
from glob import glob
from argparse import ArgumentParser
from textwrap import dedent
from datetime import datetime
from os import system, popen, getcwd, path
from mapLinks import mapLinks
from ast import literal_eval
import sys
import subprocess
from DAC import setDAC_multi
from pprint import pprint
from sendCommands import send_commands

def qieScan(outDir, linkMask = 0, serialNum = 1, uHTR = 1, pointF = "full_hb_scan_test.txt"):

    originalSTDOUT = sys.stdout

    stdOutDump = open("%s/calibrationScanOutput.stdout"%outDir, 'w')
    sys.stdout = stdOutDump

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
    cmds = ["source %s/setenv.sh; uHTRtool.exe 192.168.41.%d < uHTRcommands.txt" % (getcwd(), uHTR*4)]
    output = subprocess.Popen(cmds, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print output.communicate()[0]

    #popen("source %s/setenv.sh; uHTRtool.exe 192.168.41.%d < uHTRcommands.txt" % (getcwd(), uHTR*4)).read()
    # system("source %s/setenv.sh; uHTRtool.exe 192.168.41.%d < uHTRcommands.txt" % (getcwd(), uHTR*4))
    print "mv QIECalibration_%s.root %s" % (serialNum, outDir)
    
    cmds = ["mv QIECalibration_%s.root %s" % (serialNum, outDir)]

    output = subprocess.Popen(cmds, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print output.communicate()[0]


    print setDAC_multi(0,quiet=True)

    sys.stdout = originalSTDOUT
    return stdOutDump

def QIECalibration(topDir = "data", cardLayout = "cardLayout.txt", doFit = False, saveGraphs=False, skipShunts = False, shortShunts = False, fineScan = False):

    originalSTDOUT = sys.stdout

    if not path.exists(cardLayout):
        print "Cannot find card layout file %s!" % cardLayout
        sys.exit()



    with open(cardLayout, "r") as f:
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
    system("mkdir -p %s/%s" % (topDir, today))

    dataDir = "%s/%s" % (topDir, today)

    # Run number to create
    run = len(glob("%s/Run*" % dataDir)) + 1

    # Create run directory
    runDir = "%s/Run_%d/" % (dataDir, run)
    system("mkdir -p %s" % runDir)
    
    # Test that server is still alive
    try:
        serverCheck = send_commands(cmds = ["get %s-4-1-UniqueID" % RBX])
        if len(serverCheck) == 0 or serverCheck[0]["result"].find("0x") < 0 or serverCheck[0]["result"].find("connection failed") >= 0:
            raise StandardError 
    except StandardError:
        # Server crashed. Abort
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print "%s, Unable to communicate with ngccm server. Restart server and redo calibration scan." % timestamp
        return ""
    
    print "%s, Running Mapping Script"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print "       If this takes longer than 5 minutes, the uHTR is likely stuck and needs to be reset"
    # Map links
    histoMap = mapLinks(outF = runDir + "histoMap.txt", configFile = cardLayout, tmpDir = runDir + ".tmpLinkMap")
    sys.stdout = originalSTDOUT
    
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
    if skipShunts:
        pointF = "noshunt_hb_scan_test.txt"
    if shortShunts:
        pointF = "shortShunt_hb_scan_test.txt"
    if fineScan:
        pointF = "noshunt_hb_fine_scan_test.txt"
        
    print "%s, Starting Calibration Scan"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print "       This will take approximately 20-30 minutes"

    stdOutDump = qieScan(outDir = runDir, linkMask = linkMask, serialNum = serialNum, uHTR = uHTR, pointF = pointF)
    
    # Test that server is still alive
    try:
        serverCheck = send_commands(cmds = ["get %s-4-1-UniqueID" % RBX])
        if len(serverCheck) == 0 or serverCheck[0]["result"].find("0x") < 0 or serverCheck[0]["result"].find("connection failed") >= 0:
            raise StandardError 
    except StandardError:
        # Server crashed. Abort
        sys.stdout = stdOutDump
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print "%s, Unable to communicate with ngccm server. Restart server and redo calibration scan." % timestamp
        sys.stdout = originalSTDOUT
        print "%s, Unable to communicate with ngccm server. Restart server and redo calibration scan." % timestamp
        return ""
    
    sys.stdout = originalSTDOUT
    # Compute fits
    if doFit:
        print "%s, Staring Fit"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        system("./RedoFit_linearized_2d.py -d %s%s%s%s" % (runDir, " --saveGraphs" if saveGraphs else "", " --shuntList [1]" if skipShunts else ""," --shuntList [1,6,11.5]" if shortShunts else ""))

    return runDir

if __name__ == "__main__":
    parser = ArgumentParser("QIE Calibration Scan")
    parser.add_argument('-d', dest="topDir", default="data", help="top level directory to store qie scan data and fits")
    parser.add_argument('-c', '--cardLayout', default="cardLayout.txt", help="text file specifying teststand layout")
    #parser.add_argument('--noscan', action = "store_true", help = "process existing scan"
    parser.add_argument('--fit', action="store_true", help="run fits after qie scan")
    parser.add_argument('--saveGraphs', action="store_true", help="save graphs from fits")
    parser.add_argument('--skipShunts', action="store_true", help="skip shunts")
    parser.add_argument('--shortShunts', action="store_true", help="run only shunts 1, 6, & 11.5")
    parser.add_argument('--fineScan',action="store_true",default=False,help="Run a fine scan over range 3")
    args = parser.parse_args()

    QIECalibration(topDir = args.topDir, cardLayout = args.cardLayout, doFit = args.fit, saveGraphs=args.saveGraphs, skipShunts = args.skipShunts, shortShunts = args.shortShunts, fineScan = args.fineScan)

