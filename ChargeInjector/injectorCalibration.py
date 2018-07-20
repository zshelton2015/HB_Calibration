#!/usr/bin/env python
import os
import sys
from datetime import datetime
from LinuxGPIB import Keithley
from DAC import setDAC, setDAC_multi
from chargeInjectionPlots import plotQIcalibration
import pickle
import sqlite3

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
            sys.stdin.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def main():
    #dacSettings = range(0, 100, 25) + range(100, 1000, 100) + range(1000, 43000, 3000)
    dacSettings = [50, 1000, 10000]
    
    kam = Keithley(timeDelay=3, numReadings=15)
    results = {}
    try:
        board = int(raw_input("Enter board number: "))
        if board < 0: raise ValueError 
    except:
        print "Invalid board number"
        sys.exit()

    getch = _Getch()
    instructions = "(Press (q) to quit, (r) to redo last reading, any other key to continue)"
    
    chan = 1 
    while chan < 17:
    #chan = 6
    #while chan < 7:
        print "Set channel %d.. " % chan, instructions
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
        
        # Ensure proper channel switch is selected (desired ch set low, others set high)
        cm = "".join("%d:50000," % i for i in xrange(1,17) if i != chan)
        cm += "%d:2000" % chan
        setDAC_multi(cm, quiet=True)
        chTest = kam.read(quiet=True)

        if abs(chTest["mean"]) > 0.001 or abs(chTest["mean"]) < 0.0000001:
            # Incorrect channel(s) selected
            print "Incorrect adapter channel selected!"
            continue
        
        results[chan] = {}
        for val in dacSettings:
            #setDAC_multi("%d:%d" % (chan,val))
            setDAC(val)
            print ""
            results[chan][val] = kam.read()
            print ""
        chan += 1

        print ""
    
    if chan < 17:
        # Exited early. Don't save results
        return


    parentDir = "InjectorCalibration_highCurrent"
    boardDir = "%s/board_%d" % (parentDir, board)
    os.system("mkdir -p %s" % parentDir)
    #with open(outDir + "/board_1.pkl", "rb") as f:
    #    x = pickle.load(f)
    #    results = pickle.load(f)

    fitParams = plotQIcalibration(results, outDir = boardDir, currentMode = "high") 
    with open("%s/board_%d.pkl" % (boardDir,board), "wb") as pf:
        pickle.dump(fitParams, pf)
        pickle.dump(results, pf)
    
    
    # Write calibration parameters to database file
    calibDB = sqlite3.connect("%s/calib_QIboard_%d.db" % (boardDir, board))
    cursor = calibDB.cursor()
    cursor.execute("drop table if exists ChargeInjectorCalibrations")
    cursor.execute("create table if not exists ChargeInjectorCalibrations(board INT, channel INT, slope REAL, offset REAL)")
    for ch in sorted(fitParams.keys()):
        cursor.execute("insert into ChargeInjectorCalibrations values (?, ?, ?, ?)", (board, ch, fitParams[ch]["slope"], fitParams[ch]["offset"]))

    cursor.close()
    calibDB.commit()
    calibDB.close()

    if board > 0 and board < 16:
        # Write to master calibration file
        calibDB = sqlite3.connect("%s/ChargeInjectorCalibrations.db" % parentDir)
        cursor = calibDB.cursor()
        cursor.execute("create table if not exists ChargeInjectorCalibrations(board INT, channel INT, slope REAL, offset REAL)")
        for ch in sorted(fitParams.keys()):
            cursor.execute("select rowid from ChargeInjectorCalibrations where board = ? and channel = ?", (board,ch))
            if cursor.fetchall():
                print "Replacing data for board %d channel %d in %s/ChargeInjectorCalibrations.db" % (board, ch, parentDir)
                cursor.execute("update ChargeInjectorCalibrations set slope = ?, offset = ? where board = ? and channel = ?", (fitParams[ch]["slope"], fitParams[ch]["offset"], board, ch)) 
            else:
                cursor.execute("insert into ChargeInjectorCalibrations(board, channel, slope, offset) values (?, ?, ?, ?)", (board, ch, fitParams[ch]["slope"], fitParams[ch]["offset"]))

        cursor.close()
        calibDB.commit()
        calibDB.close()
    else:
        print "Board %d calibrations will not be saved in master database (for boards 1-15 only)"

    with open("%s/board_%d.txt" % (boardDir, board), "w+") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write("Board %d\t%s\n" % (board, timestamp))
        
        for chan in sorted(fitParams.keys()): 
            f.write("\nChannel %d\n" % chan) 
            f.write("DAC\t\tMean\t\tSigma\t\tMin\t\tMax\n")
            for dac in dacSettings:
                res = results[chan][dac]
                f.write("%d\t%s%e\t%e\t%s%e\t%s%e\n" % (dac, " " if res["mean"] > 0 else "", res["mean"], res["std"], " " if res["min"] > 0 else "", res["min"], " " if res["max"] > 0 else "", res["max"]))
            f.flush()
            f.write("\n")
        print "done!"

    with open("%s/summary_board_%d.txt" % (boardDir,board), "w+") as f:
        f.write("Fit Parameters in fC (offset, slope)\n")
        for chan in sorted(fitParams.keys()):
            f.write("%g\t\t%g\n" % (fitParams[chan]["offset"], fitParams[chan]["slope"]))
        
        f.write("\n\n" + str(results))
    

if __name__ == "__main__":
    sys.exit(main())
