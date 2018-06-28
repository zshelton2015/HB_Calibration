#!/bin/bash

echo "put HB2-[1-4]-QIE[1-64]_FixRange 256*0" > serverCommands.txt
echo "put HB2-[1-4]-QIE[1-64]_RangeSet 256*0" >> serverCommands.txt
echo "put HB2-[1-4]-QIE[1-64]_Gsel 256*0" >> serverCommands.txt
echo "quit" >> serverCommands.txt

cat serverCommands.txt

ngFEC.exe -p 64000 -H cmsnghcal01.fnal.gov -z < serverCommands.txt
