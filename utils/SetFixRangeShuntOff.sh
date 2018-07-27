#!/bin/bash

echo "put HB2-[3-4]-QIE[1-64]_FixRange 128*0" > serverCommands.txt
echo "put HB2-[3-4]-QIE[1-64]_RangeSet 128*0" >> serverCommands.txt
echo "put HB2-[3-4]-QIE[1-64]_Gsel 128*0" >> serverCommands.txt
echo "wait 200" >> serverCommands.txt
echo "quit" >> serverCommands.txt

cat serverCommands.txt

ngFEC.exe -p 64000 -H cmsnghcal01.fnal.gov -z < serverCommands.txt
