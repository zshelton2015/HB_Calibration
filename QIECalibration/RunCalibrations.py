#!/usr/bin/env python
import sys
from datetime import datetime
import sys
import subprocess

people = {'Brooks':'Brooks McMaster',
          'Bryan':'Bryan Caraway',
          'Caleb':'Caleb Smith',
          'Chris':'Chris Madrid',
          'Danny':'Danny "HF" Noonan',
          'Frank':'Frank Jensen',
          'Grace':'Grace Cummings',
          'Joe':'Joe Pastika',
          'Ian':'Ian McAlister',
          'Kamal':'Kamal Lamichhane',
          'Loriza':'Loriza Hasa',
          'Mark':'Mark Saunders',
          'Nadja':'Nadja Strobbe',
          'Nesta':'Nesta Lenhert',
          'Sezen':'Sezen Sekmen',
          'ZachE':'Zach Eckert',
          'Eckert':'Zach Eckert',
          'ZachS':'Zach Shelton',
          'Shelton':'Zach Shelton',
          }

import pprint

if not len(sys.argv)==2:
    print 'Need to specify tester name as one and only argument to the script'
    sys.exit()
else:
    tester = sys.argv[1]
    if not tester in people:
        print 'Tester name %s not recognized'%tester
        print 'Needs to be one of the keys from the following dictionary:'
        pprint.pprint(people)
        sys.exit()
    tester = people[tester]
        


originalSTDOUT = sys.stdout


print "%s, Initializing Teststand"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
import initTeststand
import time
initTeststand.resetBackplane(rbx = "HB2", port=64000, host="cmsnghcal01.fnal.gov")
time.sleep(2)
initTeststand.initLinks(uHTRslot=3,readDelay=192)
time.sleep(10)

sys.stdout = originalSTDOUT

import QIECalibrationScan

print "%s, Starting Calibration Run"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')

runDir = QIECalibrationScan.QIECalibration()
if runDir == "":
    # ngccm server crashed. Abort
    sys.stdout = originalSTDOUT
    sys.exit()

sys.stdout = originalSTDOUT

print '#'*40
print '#'*40
print '#'*40
print '#'*2
print '#'*2, " DONE WITH SCAN, STARTING FIT"
print '#'*2
print '#'*2, " CARDS CAN BE REMOVED FROM BACKPLANE"
print '#'*2
print '#'*40
print '#'*40
print '#'*40


import RedoFit_linearized_2d

sys.stdout = originalSTDOUT
print "%s, Finished Scan"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print "%s, Starting Fits"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
RedoFit_linearized_2d.QIECalibrationFit(_Directory=runDir, _saveGraphs = False, logOutput = True)

import SummaryPlot

runInfo = runDir.split("/")

runDate = runInfo[1]
runNumber = int(runInfo[2].split("_")[1])

sys.stdout = originalSTDOUT

print "%s, Starting Summary Plots"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
SummaryPlot.SummaryPlot(runAll = True, date1=[runDate], run1=[runNumber], shFac=True, images=True, tester1 = tester, logoutput = True)
print "%s, Final Merge Beginning"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#Final Merge Goes Here
from finalImages import finalImages
finalImages(runDir)

# Save TGraph Image to submission plots directory for each failure mode
from saveOnFail import saveOnFail
saveOnFail(runDir)
print "%s, Completeted Calibration and Analisys"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')

subprocess.check_call("./databaseUpload.sh %s"%runDir,shell=True)
