#!/usr/bin/env python

import numpy as np

import serial
import sys

port = sys.argv[1]
speed = 115200


np.set_printoptions(precision=2)

# Mg,632.082,-731.305,-161.944,Ac,240,0,-484,Gy,240,0,-484,^M

sp = serial.Serial(port, speed)

def xyz2rtp(a):
#    print a, a.shape
    r = np.linalg.norm(a)
    t = np.rad2deg(np.arctan2(a[1], a[0]))
    p = np.rad2deg(np.arctan2(a[2], a[1]))

    return (r,t,p)

for l in sp:
    try:
        fields = l.split(",", 12)
        #print list(enumerate(fields))
        #    continue
        magnet = np.array(map(float, fields[1:4]))
        accel  = np.array(map(float, fields[5:8]))
        gyro   = np.array(map(float, fields[9:12]))

        if len(gyro) != 3:
            continue


        #print magnet, accel, gyro

        #print "%0.2f\t%0.2f\t%0.2f" % tuple(xyz2rtp(magnet).tolist())

        s = ""
        s += "%0.2f\t%0.2f\t%0.2f" % xyz2rtp(magnet)

        a = np.rad2deg(np.arctan2(magnet[2], magnet[0]))
        s += "\t%0.2f" % a


        s += "\t\t"
        s += "%0.2f\t%0.2f\t%0.2f" % xyz2rtp(accel)
        s += "\t\t"    
        s += "%0.2f\t%0.2f\t%0.2f" % xyz2rtp(gyro)

        print s
    
    except ValueError:
        pass
