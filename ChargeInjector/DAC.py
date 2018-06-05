#!/usr/bin/env python
import os
import sys
import argparse
import subprocess
from time import sleep

"""
def setDAC( dacValue = 0, dacChannel = -1,relayOn = False):
    if relayOn==True:
        os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital; /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector -dOn -o {0} -c {1}".format(dacValue, dacChannel) )
    else:
        os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital; /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector -dOff -o {0} -c {1}".format(dacValue, dacChannel) )
    sleep(2)
"""

def setDAC( dacValue = 0):
    os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital; /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector -o %d" % dacValue)
    sleep(1)


def setDAC_multi( cm = "", dm = 0 ):
    if cm != "":
        cm = " -cm " + cm
    dm = " -dm " + str(dm)
    os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital; /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector %s" % (cm + dm) )
    sleep(1)


def setDAC_cmd(command):
    os.system("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital; /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector %s" % command )
    sleep(1)

def getDACNumber():
    count = 0
    foundDevice = False
    while not foundDevice and count < 5:
        command = "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib::/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital; /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector -o 0"
        #command = "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib::/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital; /home/hcalpro/dnoonan/mcc-libhid/dacQinjector -o 0"
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]

        outLines = output.split('\n')
        foundDevice = False
        dacNum = '00'
        for line in outLines:
            if 'USB 3105 Device is found' in line:
                    foundDevice = True
            if 'DAC Serial Number' in line:
                number = line.split()[-1]
                if number == '00101659':
                    dacNum = '01'
                if number == '00104076':
                    dacNum = '02'				
                if number == 'Error':
                    foundDevice = False
                    count += 1
                    print outLines
    if not foundDevice:
        print "!!! Unable to find USB DAC !!!"
        print "Exiting"
        print count
        #sys.exit()
    if dacNum == '00':
        print "Unknown DAC"
        print "Exiting"
        print outLines
        #sys.exit()

    print 'Using DAC %s' %dacNum
    return dacNum


if __name__=='__main__':
    parser = argparse.ArgumentParser("Set DAC values")
    parser.add_argument('-o', '--dacValue', dest='dacValue', metavar='value', help='dac value  [0-65535]', type=int, default=0)
    parser.add_argument('-d', dest='digMulti', metavar='D', help='digital I/O channels set to ON', nargs='+', choices=xrange(8), type=int)
    parser.add_argument('-c', '--channel', dest='chan', metavar='C', help='analog I/O channel to set ', choices=xrange(16), type=int)
    parser.add_argument('-cm', '--chanMulti', dest='chanMulti', metavar='c1:v1[,c2:v2,...]', help='analog I/O channels and dac values to set ')
    parser.add_argument('-b', dest='blink', help='blink LED (will override other options)', default=False, action='store_true')
   
    # If arg -b found, ignore others and blink LED
    if '-b' in sys.argv:
        setDAC('-b')
        sys.exit()
    
    args = parser.parse_args()
    if not args.dacValue in xrange(2**16):
        print "Invalid dacValue value. Range: [0-65535]"
        sys.exit()


    d = ""
    opt_c = ""
    opt_dm = ""
    if args.chanMulti is not None:
        if args.chan is not None:
            print "Warning: option -cm will overwrite -c!"
        opt_c = " -cm %s" % args.chanMulti
    if args.chan is not None:
        opt_c = " -c %s" % args.chan
    
    if args.digMulti is not None:
        for x in xrange(8):
            d = ("1" if x in args.digMulti else "0") + d
        opt_dm = " -dm %s" % eval("0b%s" % d)
    else:
        opt_dm = " -dm 0"

    cmdArgs = "-o " + str(args.dacValue) + opt_dm + opt_c# + " -verbose"
    
    #getDACNumber()
    
    setDAC_cmd(cmdArgs)
    
    """
    if len(sys.argv)==2:
	setDAC(sys.argv[1])

    if len(sys.argv)==3:
	setDAC(sys.argv[1],sys.argv[2])

    if len(sys.argv)==4:
	setDAC(sys.argv[1],sys.argv[2],eval(sys.argv[3]))
    """
