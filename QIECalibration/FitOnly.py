#!/usr/bin/env python

from datetime import datetime
import sys
import subprocess

import argparse
parser = argparse.ArgumentParser(description='Redo a fit for a specific run')
parser.add_argument('-t','--tester',dest="tester",help="Name of the tester")
parser.add_argument('-d','--dir',dest="directory",help="Name of the directory for the run data")
parser.add_argument('--upload',action='store_true',dest='upload',default=False,help="Upload results of the fit to the testing database")

options = parser.parse_args()




people = {'Brooks':'Brooks McMaster',
          'Bryan':'Bryan Caraway',
          'Caleb':'Caleb Smith',
          'Chris':'Chris Madrid',
          'Danny':'Danny "HF" Noonan',
          'Frank':'Frank Jensen',
          'Grace':'Grace Cummings',
          'Joe':'Joe Pastika',
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
if not options.tester in people:
    print 'Tester name %s not recognized'%options.tester
    print 'Needs to be one of the keys from the following dictionary:'
    pprint.pprint(people)
    sys.exit()
tester = people[options.tester]
        


originalSTDOUT = sys.stdout

runDir = options.directory

import RedoFit_linearized_2d

print "%s, Starting Fits"%datetime.now().strftime('%Y-%m-%d %H:%M:%S')
RedoFit_linearized_2d.QIECalibrationFit(_Directory=runDir, _saveGraphs = True, logOutput = True)

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

if options.upload:
    subprocess.check_call("./databaseUpload.sh %s"%runDir,shell=True)
