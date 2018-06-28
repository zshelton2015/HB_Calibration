#!/usr/bin/env python

################################################################
#  Compares calibration parameters (slope,offset) from 2 runs  #
################################################################

import os
from ROOT import *
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-x", "--file1", help="first input file" )
parser.add_argument("-y", "--file2", help="second input file" )
parser.add_argument("-o", "--dir", dest="outDir", default="compareFits", help="output directory" )

args = parser.parse_args()

if args.outDir[-1] == "/":
    args.outDir = args.outDir[:-1]


f1 = TFile.Open(args.file1, "read")
f2 = TFile.Open(args.file2, "read")

slopes1 = {}
slopes2 = {}
offsets1 = {}
offsets2 = {}

for ch in xrange(1,17):
    # Given in HW numbering (1-16)
    slopes1[ch] = {}    
    slopes2[ch] = {}    
    offsets1[ch] = {}
    offsets2[ch] = {}

    for r in xrange(2):
        slopes1[ch][r] = {}
        slopes2[ch][r] = {}
        offsets1[ch][r] = {}
        offsets2[ch][r] = {}
        for c in xrange(4):
            exec("t1 = f1.Get('fitLines/fit_LinADCvsfC_%d_range_%d_shunt_1_0_capID_%d_linearized').Clone()" % (ch, r, c) )
            exec("t2 = f2.Get('fitLines/fit_LinADCvsfC_%d_range_%d_shunt_1_0_capID_%d_linearized').Clone()" % (ch, r, c) )
            slopes1[ch][r][c] = t1.GetParameter(1)
            offsets1[ch][r][c] = t1.GetParameter(0)
            
            slopes2[ch][r][c] = t2.GetParameter(1)
            offsets2[ch][r][c] = t2.GetParameter(0)

h1_slope_r0 = TH1F("file1_slope_range0", "File1  Range 0 Slopes", 100, 0.29, 0.33)
h1_slope_r1 = TH1F("file1_slope_range1", "File1  Range 1 Slopes", 100, 0.29, 0.33)
h1_offset_r0 = TH1F("file1_offset_range0", "File1  Range 0 Offsets", 100, -20., 20.)
h1_offset_r1 = TH1F("file1_offset_range1", "File1  Range 1 Offsets", 100, -20., 20.)

h1_slope_r0.GetXaxis().SetTitle("slope")
h1_slope_r1.GetXaxis().SetTitle("slope")
h1_offset_r0.GetXaxis().SetTitle("offset") 
h1_offset_r1.GetXaxis().SetTitle("offset")

h2_slope_r0 = TH1F("file2_slope_range0", "File2  Range 0 Slopes", 100, 0.29, 0.33)
h2_slope_r1 = TH1F("file2_slope_range1", "File2  Range 1 Slopes", 100, 0.29, 0.33)
h2_offset_r0 = TH1F("file2_offset_range0", "File2  Range 0 Offsets", 100, -20., 20.)
h2_offset_r1 = TH1F("file2_offset_range1", "File2  Range 1 Offsets", 100, -20., 20.)

h2_slope_r0.GetXaxis().SetTitle("slope")
h2_slope_r1.GetXaxis().SetTitle("slope")
h2_offset_r0.GetXaxis().SetTitle("offset") 
h2_offset_r1.GetXaxis().SetTitle("offset")

hdiff_slope_r0 = TH1F("diff_slope_range0", "File1 - File2  Range 0 Slopes", 100, -0.02, 0.02)
hdiff_slope_r1 = TH1F("diff_slope_range1", "File1 - File2  Range 1 Slopes", 100, -0.02, 0.02)
hdiff_offset_r0 = TH1F("diff_offset_range0", "File1 - File2  Range 0 Offsets", 100, -10., 10.)
hdiff_offset_r1 = TH1F("diff_offset_range1", "File1 - File2  Range 1 Offsets", 100, -10., 10.)


h2d_slope_r0 = TH2F("2d_slope_range0", "Range 0 Slopes", 100, 0.29, 0.33, 100, 0.29, 0.33)
h2d_slope_r1 = TH2F("2d_slope_range1", "Range 1 Slopes", 100, 0.29, 0.33, 100, 0.29, 0.33)
h2d_offset_r0 = TH2F("2d_offset_range0", "Range 0 Offsets", 100, -10., 10., 100, -10, 10.)
h2d_offset_r1 = TH2F("2d_offset_range1", "Range 1 Offsets", 100, -20., 20., 100, -20, 20.)

h2d_slope_r0.GetXaxis().SetTitle("File1 Slope") 
h2d_slope_r0.GetYaxis().SetTitle("File2 Slope")
h2d_slope_r1.GetXaxis().SetTitle("File1 Slope") 
h2d_slope_r1.GetYaxis().SetTitle("File2 Slope")

h2d_offset_r0.GetXaxis().SetTitle("File1 Offset") 
h2d_offset_r0.GetYaxis().SetTitle("File2 Offset")
h2d_offset_r1.GetXaxis().SetTitle("File1 Offset") 
h2d_offset_r1.GetYaxis().SetTitle("File2 Offset")

for ch in xrange(9,16):
    for cap in xrange(4):
        h1_slope_r0.Fill(slopes1[ch][0][cap])
        h1_slope_r1.Fill(slopes1[ch][1][cap])
        h1_offset_r0.Fill(offsets1[ch][0][cap])
        h1_offset_r1.Fill(offsets1[ch][1][cap])
        
        h2_slope_r0.Fill(slopes2[ch][0][cap])
        h2_slope_r1.Fill(slopes2[ch][1][cap])
        h2_offset_r0.Fill(offsets2[ch][0][cap])
        h2_offset_r1.Fill(offsets2[ch][1][cap])

        hdiff_slope_r0.Fill(slopes1[ch][0][cap] - slopes2[ch][0][cap])
        hdiff_slope_r1.Fill(slopes1[ch][1][cap] - slopes2[ch][1][cap])
        hdiff_offset_r0.Fill(offsets1[ch][0][cap] - offsets2[ch][0][cap])
        hdiff_offset_r1.Fill(offsets1[ch][1][cap] - offsets2[ch][1][cap])

        h2d_slope_r0.Fill(slopes1[ch][0][cap], slopes2[ch][0][cap])
        h2d_slope_r1.Fill(slopes1[ch][1][cap], slopes2[ch][1][cap])
        h2d_offset_r0.Fill(offsets1[ch][0][cap], offsets2[ch][0][cap])
        h2d_offset_r1.Fill(offsets1[ch][1][cap], offsets2[ch][1][cap])

os.system("mkdir -p %s" % args.outDir)
outF = TFile.Open("%s/%s.root" % (args.outDir, args.outDir), "recreate")

h1_slope_r0.Write()
h1_slope_r1.Write()
h1_offset_r0.Write()
h1_offset_r1.Write()
h2_slope_r0.Write()
h2_slope_r1.Write()
h2_offset_r0.Write()
h2_offset_r1.Write()
hdiff_slope_r0.Write()
hdiff_slope_r1.Write()
hdiff_offset_r0.Write()
hdiff_offset_r1.Write()
h2d_slope_r0.Write()
h2d_slope_r1.Write()
h2d_offset_r0.Write()
h2d_offset_r1.Write()

outF.Close()
