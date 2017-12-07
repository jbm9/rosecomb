from collections import defaultdict

import socket
import sys

class Squitter:
    def __init__(self, addr=None):
        self.addr = addr
        
        self.flight = None

        self.identity = None
        
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0
        
        self.track = 0
        self.speed = 0
        self.vr = 0

        self.last_printed = None
        
    def seen(self):
        self.last_seen = time.time()


    def __str__(self):
        return "(%6s) %7s: (%0.1f, %0.1f)@%d, %d at %d knots, vr=%d" % (self.addr, self.flight,
                                                                      self.lat, self.lon,
                                                                      self.alt,
                                                                      self.track, self.speed,
                                                                      self.vr)

class ADSBListener:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

        self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fd.connect((hostname, port))

        self.buf = ""

        self.planes = defaultdict(Squitter)

    def _poll(self):
        b2 = self.fd.recv(1024)
        while b2 and (len(self.buf) < 1024):
            self.buf += b2
            b2 = self.fd.recv(1024)

        lines = self.buf.split("\n")
        self.buf = lines[-1]

        for l in lines[:-1]:
            try:
                self._proc(l)
            except ValueError:
                pass
            except:
                fields = l.split(",")
                print "BOGON: %s/%s (%s): %s" % (fields[0], fields[1], len(fields), str([ (i,s) for i,s in enumerate(fields) if s and s != '0' and i > 4]))
                
    def _proc(self, l):
        fields = l.split(",")

        if "MSG" != fields[0]:
            raise ValueError("Expected field[0] to be MSG")

        typ = fields[1]
        addr = fields[4]
        if len(addr) != 6:
            raise ValueError("Address length is malformed")

        plane = self.planes[addr]
        plane.addr = addr
        plane.seen()

        if typ == '1':
            plane.flight = fields[10]
        elif typ == '3':
            plane.lat = float(fields[14])
            plane.lon = float(fields[15])
            plane.alt = float(fields[11])
        elif typ == '4':
            plane.track = float(fields[12])
            plane.speed = float(fields[13])
            plane.vr = float(fields[16])
        elif typ == '5':
            if len(fields) == 22:
                plane.alt = float(fields[11])
        elif typ == '6':
            plane.identity = fields[17]
        elif typ == '8':
            plane.lat = float(fields[14])
            plane.lon = float(fields[15])
        else:
            print [ (i,s) for i,s in enumerate(fields) if s and s != '0' ]
        
            # print "%s: %s" % (addr, l)
            sys.stdout.flush()

        if plane.last_printed < (time.time() - 3):
            print plane
            plane.last_printed = time.time()


if __name__ == '__main__':
    import time
    al = ADSBListener('localhost', 30003)
    while True:
        al._poll()
        time.sleep(1)
