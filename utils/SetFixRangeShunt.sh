#!/bin/bash

range=$1
shunt=$2


(>&2 echo "    Starting range $range shunt $shunt")


echo "put HB2-[3-4]-QIE[1-64]_FixRange 128*1" > serverCommands.txt
echo "put HB2-[3-4]-QIE[1-64]_RangeSet 128*$range" >> serverCommands.txt
echo "put HB2-[3-4]-QIE[1-64]_Gsel 128*$shunt" >> serverCommands.txt
echo "wait 200" >> serverCommands.txt
echo "quit" >> serverCommands.txt

cat serverCommands.txt

ngFEC.exe -p 64000 -H cmsnghcal01.fnal.gov -z < serverCommands.txt
