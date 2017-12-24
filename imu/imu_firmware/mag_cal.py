#!/usr/bin/env python

# This is used to check the calibration values for the magnetometer.
# Set it up to do raw readings, then hold the board in all possible
# orientations for equal amounts of time (either put it in a random
# hamster ball somehow, or hold it in all four quadrants in both
# orientations about each axis.  I do the latter, counting to three in
# each orientation.
#
# Adjust these offsets until you get 0,0,0 at the end of that result


offsets = [3210,-4270,-550]


import numpy as np

import serial
import sys

port = sys.argv[1]
speed = 115200


np.set_printoptions(precision=2)

# Mg,632.082,-731.305,-161.944,Ac,240,0,-484,Gy,240,0,-484,^M

sp = serial.Serial(port, speed)


vals = [0,0,0]
n = 0.0

for l in sp:
    try:
        fields = l.split(",", 4)
        if fields[0] != 'MR':
            continue

        for i in range(1,4):
            vals[i-1] += int(fields[i]) - offsets[i-1]

        n += 1
        
        print [ int(v/n) for v in vals ]
    except Exception, e:
        print e
        pass
