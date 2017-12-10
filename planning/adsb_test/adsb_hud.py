#!/usr/bin/env python

# A quick and janky HUD for ADS-B data.
#
# To use this, run dump1090 as so:
#   ./dump1090  --net --enable-agc
#   (I also use --device-index 1 --interactive --interactive-rows 30 )
# This will set up a listener on your localhost that the following connects to.

import time
import numpy as np

from adsb_listener import ADSBListener

from eci import *


OBS_LOC = (np.deg2rad(37.728206),np.deg2rad(-122.407863), 25) # lat,long,alt (meters)
OBS_HEADING = (10.0, 62.0) # alt,az, degrees
OBS_FOV = (15.0,15.0) # span of view, degrees

ADSB_HOST = "localhost"
ADSB_PORT = 30003


class ECIPlanePoint(ECIEarthPoints):
    def __init__(self, plane):
        self.plane = plane
        self._update()

    def _update(self):
        self.lat = np.deg2rad(self.plane.lat)
        self.lon = np.deg2rad(self.plane.lon)
        self.alt = self.plane.alt*0.3048/1e3 # convert to metrique
        
        
    def at(self, t):
        self._update()

        # Get our basic position
        ept = ECIEarthPoints.at(self,t)

        return ept


PLANES = {} # addr => ECIPP(plane)
qth = ECIEarthPoints(OBS_LOC[0], OBS_LOC[1], OBS_LOC[2])
qth_pt = qth.at(0)

def plane_spotted(plane):
    PLANES[plane.addr] = ECIPlanePoint(plane)
    if plane.last_printed < (time.time() - 3) and (plane.last_printed < plane.pos_ts or plane.last_printed < plane.vector_ts):
#        if plane.flight:
#            print plane
        if plane.lat != 0:
            pt = PLANES[plane.addr].at(0)
            
            alt,az = map(np.rad2deg, qth.alt_az(0, pt))
            d = np.linalg.norm(qth_pt.range_to(pt))
            r2 = qth_pt.range_to(pt)

            flag = "    "
            if alt > 10 and d < 50 and az > 0 and az < 120:
                flag = "*** "
            print "%s[%s] alt=%0.2f az=%0.2f d=%0.1f el=%d (%0.3f,%0.3f) / (%0.3f, %0.3f)" % (flag, plane.flight if plane.flight else "#" + plane.addr, alt, az, d, plane.alt, plane.lat, plane.lon, plane.lat - np.rad2deg(qth.lat), plane.lon - np.rad2deg(qth.lon))
        plane.last_printed = time.time()

    
al = ADSBListener('localhost', 30003, plane_spotted)
while True:
    al._poll()
    time.sleep(0.001)
    deleted = al.expire(time.time() - 10)
    for addr in deleted:
        print "         Expired %s" % addr

