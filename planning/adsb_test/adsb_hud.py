#!/usr/bin/env python

# A quick and janky HUD for ADS-B data.
#
# To use this, run dump1090 as so:
#   ./dump1090  --net --enable-agc
#   (I also use --device-index 1 --interactive --interactive-rows 30 )
# This will set up a listener on your localhost that the following connects to.


# Do the config load before importing cv2, as it's slow as hell.
import sys
import json

if len(sys.argv) != 2:
    print "Usage: adsb_hud.py config.json"
    sys.exit(1)

f = file(sys.argv[1])
config = json.load(f)
f.close()

import signal

import time
import numpy as np

t0 = time.time()
import cv2 # XXX Why does this take so long?!
t1 = time.time()

print "Loading cv2 took %0.3f" % (t1-t0)

from adsb_listener import ADSBListener

import os

from eci import *

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer


OBS_LOC = [np.deg2rad(config['loc']['lat']),np.deg2rad(config['loc']['lon']), config['loc']['alt']] # lat,long,alt (meters)
OBS_HEADING = [config['camera_loc']['alt'], config['camera_loc']['az']] # alt,az, degrees
OBS_FOV = config['camera']['FOV'] # span of view, degrees
OBS_PX = config['camera']['resolution']    # span of view, pixels (height, then width, because math)


def aa_deg2px(alt, az):
    # Convert alt,az in degrees to pixels on the sensor. Returns None if off-screen
    # NB: returns these in (y,x) order,to be consistent with alt/az!
    #
    d_alt = alt - OBS_HEADING[0]
    d_az = az - OBS_HEADING[1]

    # you can only be +/- 180, so fixup:
    if d_az < -180:
        d_az += 360
    elif d_az > 180:
        d_az -= 360


    p_alt = d_alt / OBS_FOV[0]/2.0
    p_az = d_az / OBS_FOV[1]/2.0

    px_alt = int(OBS_PX[0]/2.0 + p_alt*OBS_PX[0])
    px_az  = int(OBS_PX[1]/2.0 + p_az*OBS_PX[1])

    if px_alt < 0 or px_alt >= OBS_PX[0]:
        return None

    if px_az < 0 or px_az >= OBS_PX[1]:
        return None
    return (px_alt, px_az)

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

def plane_pos(pt):
    alt,az = map(np.rad2deg, qth.alt_az(0, pt))
    d = np.linalg.norm(qth_pt.range_to(pt))
    return (alt, az, d)

def plane_spotted(plane):
    PLANES[plane.addr] = ECIPlanePoint(plane)

    if plane.lat != 0 and plane.last_printed < (time.time() - 3) and \
       (plane.last_printed < plane.pos_ts or plane.last_printed < plane.vector_ts):
        pt = PLANES[plane.addr].at(0)

        alt,az,d = plane_pos(pt)
        pxpos = aa_deg2px(alt,az)
        flag = "*** " if pxpos else "    "
        if pxpos:
            flag = "*** "

        print "%s[%8s] alt=%5.2f az=%6.2f d=%5.1f el=%5d (%6.3f,%7.3f) / (%6.3f, %6.3f) / %s" % (flag, plane.flight if plane.flight else "##" + plane.addr, alt, az, d, plane.alt, plane.lat, plane.lon, plane.lat - np.rad2deg(qth.lat), plane.lon - np.rad2deg(qth.lon), pxpos)
        plane.last_printed = time.time()


def adsb_worker():
    try:
        al = ADSBListener(config['adsb']['server'], config['adsb']['port'], plane_spotted)
        while True:
            al._poll()
            time.sleep(0.001)
            deleted = al.expire(time.time() - 10)
            for addr in deleted:
                print "         Expired %s" % addr
                if addr in PLANES:
                    del PLANES[addr]
    except Exception, e:
        print "ADSB Worker Exception: %s" % e
        os.kill(os.getpid(), signal.SIGINT) # send an interrupt to kill ourself
        sys.exit(1)

import threading
d = threading.Thread(name='adsb_worker', target=adsb_worker)
d.setDaemon(True)
d.start()


curimg = None

############################################################
# HTTP Server bits


class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print self.path
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                if curimg is None:
                    return
                imgRGB = cv2.cvtColor(curimg,cv2.COLOR_GRAY2RGB)
                r, buf = cv2.imencode(".jpg",imgRGB)
                self.wfile.write("--jpgboundary\r\n")
                self.send_header('Content-type','image/jpeg')
                self.send_header('Content-length',str(len(buf)))
                self.end_headers()
                self.wfile.write(bytearray(buf))
                self.wfile.write('\r\n')
                time.sleep(0.1)
            return
        if self.path.endswith('.html') or self.path=="/":
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<img src="/cam.mjpg"/>')
            self.wfile.write('</body></html>')
            return

def http_worker():
    try:
        server = HTTPServer((config['http_server']['bindaddr'],config['http_server']['port']),CamHandler)
        print "Server started"
        server.serve_forever()
    except Exception, e:
        print "Error in HTTP Worker: %s" % e
        os.kill(os.getpid(), signal.SIGINT)


if config['http_server']['enabled']:
    http_server = threading.Thread(name='http_server', target=http_worker)
    http_server.setDaemon(True)
    http_server.start()




############################################################
# Actual main loop



cap = cv2.VideoCapture(-1)
if not cap.isOpened():
    raise Exception("Couldn't open video capture")
cap.set(3,480)
cap.set(4,640)
cap.set(15, 0.1)
flag,frame = cap.read()
if not flag:
    raise Exception("error getting initial frame")
OBS_PX[0] = frame.shape[0] # yay for backwards math notation being alt,az!
OBS_PX[1] = frame.shape[1]

print "Reset OBS_PX to %s" % OBS_PX


def brighten(img):
    p5 = np.percentile(img, 5)
    p75 = np.percentile(img, 75)

    retval = (img - p5) * 255.0/p75
    return retval


while True:
    ret,img = cap.read()

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = brighten(img) # A bit of a hail mary for crappy webcams

    any_planes = False

    for ecipp in PLANES.values():
        if ecipp.lon == 0:
            continue
        alt,az,d = plane_pos(ecipp.at(0))
        pxpos = aa_deg2px(alt,az)

        if pxpos:
            any_planes = True
            nom = ecipp.plane.flight if ecipp.plane.flight else ecipp.plane.addr

            (y,x) = pxpos
            y = OBS_PX[0] - 1 - y # origin funtime woo

            text_color = (255,0,0)
            cv2.circle(img,(x,y),5,(128,128,255),1)
            text_height = min(1.5, max(30.0/d, 0.33))
            cv2.putText(img, nom, (x,y), cv2.FONT_HERSHEY_PLAIN, text_height, text_color, thickness=1)

    cv2.putText(img,
                time.strftime("%Y-%m-%d %T %Z"),
                (0, OBS_PX[0]),
                cv2.FONT_HERSHEY_PLAIN,
                1.0,
                (0,255,0),
                thickness=1)

            #print ecipp.plane.addr, pxpos

    curimg = img
    sleep_time = 10 if any_planes else 300

    if config['run_headless']:
        time.sleep(sleep_time/1000.0)
    else:
        cv2.imshow("input", img)
        key = cv2.waitKey(sleep_time)
        if key == 27:
            break

if not config['run_headless']:
    cv2.destroyAllWindows()
cv2.VideoCapture(-1).release()
