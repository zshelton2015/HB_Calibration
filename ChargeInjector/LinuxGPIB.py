#!/usr/bin/env python
import sys
import gpib
from time import sleep
from numpy import mean,std

class Keithley:
    def __init__(self, resource=14, timeDelay=10, numReadings=20, initDelay=1):
        try:
            self.resource = int(resource)
        except ValueError:
            print "Invalid resource (numerical values only)"
            return 
        try:
            self.timeDelay = int(timeDelay)
            if self.timeDelay < 0: raise ValueError("Negative time delay setting is invalid!")
        except ValueError:
            # timeDelay negative or non-integer
            print "Invalid time delay. Setting default value of 10"
            self.timeDelay = 10

        try:
            self.numReadings = int(numReadings) 
            if self.numReadings < 0: raise ValueError("Negative number of readings is invalid!")
        except ValueError:
            print "Invalid number of readings. Setting default value of 20"
            self.numReadings = 20
        
        try:
            self.initDelay = int(initDelay)
            if self.initDelay < 0: raise ValueError("Negative init delay setting is invalid!")
        except ValueError:
            # initDelay negative or non-integer
            print "Invalid init delay. Setting default value of 1"
            self.initDelay = 1

        self.con = gpib.dev(0, self.resource)
        self.mean = 0.
        self.std = 0.
        self.min = 0.
        self.max = 0.


    def print_instrument(self):
        print "Instrument:"
        gpib.write(self.con, '*IDN?')
        print gpib.read(self.con, 1000)
        print ""    # Ensure output buffer is flushed


    def read(self, verbose=True):
        ''' Read data from instrument '''
        gpib.write(self.con, '*RST')          # restore GPIB defaults
        gpib.write(self.con, 'SYST:ZCH ON')   # enable zero check
        gpib.write(self.con, 'RANG 2e-9')     # select the 2nA range
        #gpib.write(self.con, 'DAMP ON')       # enable damping to reduce noise from high capacitance
        
        gpib.write(self.con, 'INIT ')         # Trigger reading to be used as zero correction.
        sleep(self.initDelay)
        gpib.write(self.con, 'SYST:ZCOR:ACQ') # Use last reading taken as zero correct value.
        gpib.write(self.con, 'SYST:ZCOR ON')  # Perform zero correction.
        gpib.write(self.con, 'RANG:AUTO ON')  # Enable auto range.

        gpib.write(self.con, 'SYST:ZCH OFF')  # Disable zero check.
        gpib.write(self.con, '*CLS') # Clear status model.
        
        #store readings
        #gpib.write(self.con, 'FORM:ELEM READ, UNIT') # 
        gpib.write(self.con, 'FORM:ELEM READ')
        #gpib.write(self.con, 'TRIG:DEL 2')
        gpib.write(self.con, 'TRIG:COUN %d' % self.numReadings) # Set trigger model to take to 10 readings.
        gpib.write(self.con, 'TRAC:POIN %d' % self.numReadings) # Set buffer size to 10.
        gpib.write(self.con, 'TRAC:CLE ') # Clear buffer.
        gpib.write(self.con, 'TRAC:FEED SENS ') # Store raw input readings.
        gpib.write(self.con, 'TRAC:FEED:CONT NEXT ') # Start storing readings.

        gpib.write(self.con, 'INIT') # trigger readings
        sleep(self.timeDelay)

        gpib.write(self.con,'TRAC:DATA?') # Request all stored readings
        currents_raw = gpib.read(self.con, 1000).split(',')

        currents = []
        for i in currents_raw:

            currents.append(float(i.encode('ascii','ignore')))

        print "Readings expected: %d\tReadings taken: %d" % (self.numReadings, len(currents))
        self.mean = mean(currents)
        self.std = std(currents)
        self.min = min(currents)
        self.max = max(currents)
        self.currents = currents
        if verbose:
            print 'Mean: {}'.format(self.mean)
            print 'STD : {}'.format(self.std)
            print 'Min : {}'.format(self.min)
            print 'Max : {}'.format(self.max)

        return {"mean":self.mean, "std":self.std, "min":self.min, "max":self.max}
