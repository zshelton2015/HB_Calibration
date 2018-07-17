#!/bin/bash
if [[ "$1" == "-d" ]]
then 
#  echo "HERE"
#  echo "/home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector -o $2"
  /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector -o $2 2>&1 | grep failed 
  sleep 0.25
elif [[ "$1" == "-r" ]]
then
#  cd /home/hep/ChargeInjector/CalibrationScripts/ChargeInjection
  echo "./daq.sh -r is terrible and so this now does nothing, stop using this!!"
  #./fixedrange.sh -$2
elif [[ "$1" == "-p" ]]
then
  echo "HERE 2"
  /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector $2   2>&1 | grep failed
elif [[ "$1" == "-s" ]]
then
  (>&2 echo "      Setting range ${3} shunt ${2}")
  /home/hep/HB_Calibration/utils/SetFixRangeShunt.sh $3 $2
  sleep 2
elif [[ "$1" == "-off" ]]
then
  /home/hep/HB_Calibration/utils/SetFixRangeShuntOff.sh
  sleep 2
else
  echo "HERE 3"
  /home/hep/ChargeInjector/DAC/mcc-libhid_SplitDigital/dacQinjector -o $1 > /dev/null 2>&1
fi
