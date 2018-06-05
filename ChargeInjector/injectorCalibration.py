#!/usr/bin/env python
import os
import sys
from datetime import datetime
from LinuxGPIB import Keithley
from DAC import setDAC, setDAC_multi
from chargeInjectionPlots import plotQIcalibration
import pickle

class _Getch:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def main():
    #dacSettings = [0, 50, 100, 200, 500, 1000, 5000, 10000, 20000, 30000] 
    dacSettings = range(0, 100, 25) + range(100, 1000, 100) + range(1000, 43000, 3000)
    kam = Keithley(timeDelay=3, numReadings=15)
    results = {}
    try:
        board = int(raw_input("Enter board number: "))
        if board < 0: raise ValueError 
    except:
        print "Invalid board number"
        sys.exit()

    getch = _Getch()
    print "Press (q) to quit, (r) to redo last reading, any other key to continue"
    
    chan = 1 
    while chan < 17:
        print "Set channel %d.." % chan,
        x = getch()
        if x == 'q':
            break
        elif x == 'r': 
            if chan == 0:
                print "\nNo readings taken yet!"
                continue
            else:
                chan -= 1
                print "\nRetaking channel %d.." % chan, 

        print ""
        results[chan] = {}
        for val in dacSettings:
            #setDAC_multi("%d:%d" % (chan,val))
            setDAC(val)
            results[chan][val] = kam.read()
            #results[chan][val] = [chan, val % 1000, chan+val, float(val)/(chan + 1.)]
        chan += 1

        print "done."
    
    board = 1
    outDir = "InjectorCalibration_highCurrent"
    os.system("mkdir -p %s" % outDir)
    #with open(outDir + "/board_1.pkl", "rb") as f:
    #    x = pickle.load(f)
    #    results = pickle.load(f)

    fitParams = plotQIcalibration(results, outDir = outDir, currentMode = "high") 
    with open("%s/board_%d.pkl" % (outDir,board), "wb") as pf:
        pickle.dump(fitParams, pf)
        pickle.dump(results, pf)
    default = outDir + "/board_%d.tx" % board
    outF = raw_input("Output file name (defaults to %s/board_X.tx):" % outDir)
    if outF == "":
        outF = default
    if not os.access(os.path.abspath(outF), os.W_OK):
        print "User does not have write access! Using default."
        outF = default
    if not os.path.exists(outF):
        os.system("mkdir -p %s" % os.path.dirname(outF))
        if not os.path.exists(outF):
            # Unable to create directory (likely a permission issue)
            # Revert to default
            outF = default
            os.system("mkdir -p %s" % os.path.dirname(outF))

    with open(outF, "w+") as f:
        print "Writing results to %s.." % outF,
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write("Board %d\t%s\n" % (board, timestamp))
        
        for chan in xrange(1,17):
            f.write("\nChannel %d\n" % chan) 
            f.write("DAC\t\tMean\t\tSigma\t\tMin\t\tMax\n")
            for dac in dacSettings:
                res = results[chan][dac]
                f.write("%d\t%s%e\t%e\t%s%e\t%s%e\n" % (dac, " " if res["mean"] > 0 else "", res["mean"], res["std"], " " if res["min"] > 0 else "", res["min"], " " if res["max"] > 0 else "", res["max"]))
            f.flush()
            f.write("\n")
        print "done!"

    with open("%s/summary_board_%d.tx" % (outDir,board), "w+") as f:
        f.write("Fit Parameters in fC (offset, slope)\n")
        for chan in sorted(fitParams.keys()):
            f.write("%g\t\t%g\n" % (fitParams[chan]["offset"], fitParams[chan]["slope"]))
        
        f.write("\n\n" + str(results))
    

if __name__ == "__main__":
    sys.exit(main())
