#!/usr/bin/env python
from os import system,popen
from textwrap import dedent
import sys
from time import sleep
import os
from DAC import *
import time		  
from argparse import ArgumentParser
from sendCommands import send_commands
import re
from ROOT import *
# 0x : value must start with literal '0x'
# [A-Fa-f0-0] : only values of A-F, a-f, or 0-9 allowed
# + : multiple numbers allowed
hexfind = re.compile(r"0x[A-Fa-f0-9]+")


parser = ArgumentParser()
parser.add_argument("-d", "--dir", dest="outDir", default="qiChannelMap" ,
                  help="output directory" )
parser.add_argument("-v", "--lsb", dest="lsb", default="test" ,
                  help="output filename prefix" )
parser.add_argument("-c", "--ch", dest="channel", default="1",
		  help="channel of the Qinjector")

args = parser.parse_args()
if args.outDir[-1] == "/": args.outDir = args.outDir[:-1]


def linkMap(outDir = "mapLink", uHTRlinks = range(0,24)):
    pass



def mapQIchannels(outDir = "QIchannels", QIchannels = range(1,17)):
    system( "mkdir -p %s" % outDir) 
    print "Setting ranges"
    # ngccm commands 
    # Set to FixRange mode with range 1
    ngccm_cmds = ["put HB1-[1-4]-QIE[1-64]_FixRange 256*1",
                  "put HB1-[1-4]-QIE[1-64]_RangeSet 256*1"]
    ngccm_output = send_commands(cmds = ngccm_cmds)

    UID = {1:{}, 2:{}, 3:{}, 4:{}}
    getUIDcmds = []
    for rm in xrange(1,5):
        for slot in xrange(1,5):
            getUIDcmds.append("get HB1-%d-%d-UniqueID" % (rm, slot))

    ngccm_output = send_commands(cmds = getUIDcmds)
    for line in ngccm_output:
        cmd = line["cmd"]
        # Find rm and slot number from register:  HB1-[rm]-[slot]-UniqueID
        _rm,_slot = cmd[cmd.find("HB1") + 4 : cmd.find("-UniqueID")].split('-')
        try:
            rm = int(_rm)
            slot = int(_slot)
        except ValueError:
            print "Unable to find rm,slot numbers from cmd %s" % cmd
            continue
        
        
        uidhex = hexfind.findall(line["result"])
        # Two hex values expected
        if len(uidhex) == 2:
            UID[rm][slot] = "%s_%s" % (uidhex[0], uidhex[1])
        else:
            #print "Unique ID not found for RM %d Slot %d" % (rm,slot)
            UID[rm][slot] = ""
            
    print UID 
    
    dacVal = 600
    chmaps = {}
    for ch in QIchannels:
        setDAC_multi (cm = "%d:%d" % (ch, dacVal))
        time.sleep(0.25)
        startCommands = dedent("""\
                        0
                        link
                        histo
                        clear
                        integrate
                        50
                        0
                        %s
                        0
                        quit
                        quit
                        exit
                        exit""" % (outDir + "/ch_%d_dac_%d.root" % (ch,dacVal)))
        print startCommands

            
        outputFile = open("uHTRcommands.txt","w")
        outputFile.write(startCommands)
        outputFile.close()
        
        popen("uHTRtool.exe 192.168.41.4 < uHTRcommands.txt").read()
        time.sleep(2)
        f = TFile.Open("%s/ch_%d_dac_%d.root" % (outDir,ch,dacVal))
        hnum = -1   # Histogram number of active channel, saving -1 indicates error
        for i in range(192):
            mean = eval("f.Get('h%d').GetMean()" % i)
            if mean > 30:
                # Found active channel
                hnum = i
                break
        link = hnum/8
        fibchannel = hnum%8
        chmaps[ch] = {"hist":hnum,"link":link,"channel":fibchannel}
    
    # Turn off FixRange mode
    ngccm_cmds = ["put HB1-[1-4]-QIE[1-64]_FixRange 256*0"]
    ngccm_output = send_commands(cmds = ngccm_cmds)
    
    # Set DAC value back to 0
    setDAC(0)
    return chmaps
         
    
#setDAC(0)
#runDAC_makehisto(low_val,  outputFile= "{0}/CalibrationData_card31_{1}_dac_highCurrent.root".format(options.dirName,options.channel),relayOn=True)
#runDAC_makehisto(high_val, outputFile= "{0}/CalibrationData_card31_{1}_dac_lowCurrent.root".format(options.dirName,options.channel),relayOn=False)
#
#setDAC(0)



