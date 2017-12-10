from collections import defaultdict
import time
import math
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
        self.pos_ts = 0

        self.track = 0
        self.speed = 0
        self.vr = 0
        self.vector_ts = 0

        self.last_printed = None

        self.seen()

    def seen(self):
        self.last_seen = time.time()

    def __str__(self):
        return "(%6s) %7s: (%0.1f, %0.1f)@%d, %d at %d knots, vr=%d" % (self.addr, self.flight,
                                                                      self.lat, self.lon,
                                                                      self.alt,
                                                                      self.track, self.speed,
                                                                      self.vr)

class ADSBListener:
    def __init__(self, hostname, port, cb=None):
        self.hostname = hostname
        self.port = port

        self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fd.connect((hostname, port))

        self.buf = ""

        self.planes = defaultdict(Squitter)

        self.cb = cb

    def _poll(self):
        b2 = self.fd.recv(128*1024)
        while b2 and (len(self.buf) < 1024):
            self.buf += b2
            b2 = self.fd.recv(128*1024)

        lines = self.buf.split("\n")
        self.buf = lines[-1]

        for l in lines[:-1]:
            try:
                self._proc(l)
            except ValueError:
                pass
            except Exception, e:
                fields = l.split(",")
                print "BOGON: %s/%s (%s): %s" % (fields[0], fields[1], len(fields), str([ (i,s) for i,s in enumerate(fields) if s and s != '0' and i > 4]))
                print e
                raise

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

        if typ == '1' and fields[10]:
            plane.flight = fields[10]
        elif typ == '3' and fields[14] != '0': # '' throws exceptions
            plane.lat = float(fields[14])
            plane.lon = float(fields[15])
            plane.alt = float(fields[11])
            plane.pos_ts = time.time()
        elif typ == '4':
            if fields[12] != '0':
                plane.track = float(fields[12])
            if fields[13] != '0':
                plane.speed = float(fields[13])
            if fields[16] != '0':
                plane.vr = float(fields[16])
            plane.vector_ts = time.time()
        elif typ == '5':
            if len(fields) == 22 and fields[11] != '0':
                plane.alt = float(fields[11])
                plane.pos_ts = time.time()

        elif typ == '6':
            plane.identity = fields[17]
        elif typ == '8' and fields[14] != '0':
            plane.lat = float(fields[14])
            plane.lon = float(fields[15])
            plane.pos_ts = time.time()
        else:
            print [ (i,s) for i,s in enumerate(fields) if s and s != '0' ]

            # print "%s: %s" % (addr, l)
            sys.stdout.flush()


        if self.cb:
            self.cb(plane)
        else:
            print plane


    def expire(self, t_expiry):
        todel = [ p.addr for p in self.planes.values() if p.last_seen < t_expiry ]
        for addr in todel:
            del self.planes[addr]
        return todel

if __name__ == '__main__':
    import time

    def print_plane(plane):
        if plane.last_printed < (time.time() - 1):
            print plane
            plane.last_printed = time.time()

    al = ADSBListener('localhost', 30003, print_plane)

    while True:
        al._poll()
        time.sleep(0.001)
        deleted = al.expire(time.time() - 10)
        for addr in deleted:
            print "   Expired %s" % addr
