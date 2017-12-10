import numpy as np

class GMST:
    T0_utc = 946728000 # 2000-01-01T12h00Z is the zero point for T below
    GMST0 = 18.697374558
    SID_HRS = 24.06570982441908 # Clock hours in a sideral day


    @classmethod
    def from_unix(cls, t_utc):
        """Compute GMST (in radians) based on unix time

        Based on a formula from http://aa.usno.navy.mil/faq/docs/GAST.php

        This formula is reportedly good to 0.1sec/century, which is plenty
        good for SGP4 work, where we're willing to conflate UTC and UT1, which
        is a margin of a millenium(!) of drift due to this formula.

        NB: I'm pretty sure we get all the significant figures in the constants
        here, but it's not super clear, so the drift may be higher than
        reported.  For this application, I can't be bothered to check up on this,
        but if you need super high precision, this is a bit of an XXX comment.
        """

        d = (t_utc - GMST.T0_utc)/86400.0
        gmst_h = (GMST.GMST0 + GMST.SID_HRS*d) % 24 # GMST given in 24.00 hour periods
        gmst_rad = gmst_h / 24.00*2*np.pi # 24.00 hr, so not the same as WGS84.omega
        return gmst_rad

class WGS84:
    # A container for random WGS84 constants; NB: this duplicates
    # stuff in sgp4, probably can be removed
    f = 1/298.257223560 # flattening of the spheroid, no units
    a = 6378.137 # equatorial radius, km
    omega_e = 366.25/365.25 # ratio of sidereal day to solar day
    omega = 7.292115e-5 # earth rotation rate, radians/second. Note! this is 2pi/_sidereal_ day
                        # Alternately, omega = 2*pi/86400*omega_e


class ECIPoint:
    "Represents an (x,y,z) point with velocity in the Earth-Centered Inertial coordinate system"
    def __init__(self, pos, vel):
        self.pos = np.array(pos)
        self.vel = np.array(vel)

    def speed(self):
        # Get the absolute speed of this object
        return np.sqrt(np.sum(self.vel**2))

    def range_to(self, eci2):
        # Get the range from this point to the second point
        return eci2.pos - self.pos

    def range_vel(self, eci2):
        return eci2.vel - self.vel

    def __repr__(self):
        return "(%0.3f,%0.3f,%0.3f) km @ (%0.3f,%0.3f,%0.3f) km/s" % (self.pos[0],
                                                                      self.pos[1],
                                                                      self.pos[2],
                                                                      self.vel[0],
                                                                      self.vel[1],
                                                                      self.vel[2])

class ECIEarthPoints:
    "Given a lat/long and altitude, compute an ECIPoint for any given unix time."
    def __init__(self, lat, lon, alt_m):
        """Create an ECIPoint generator for the given position.

        * (lat,lon) in radians, because degress includes further decimal vs hms arbitrariness
        * alt above earth radius in meters
        """
        self.lat = lat
        self.lon = lon
        self.alt = alt_m/1e3 # Convert to km

    def lmst(self, t):
        # Get the local sideral mean time for unix time t, in radians

        gmst = GMST.from_unix(t)
        theta = gmst + self.lon # local mean sidereal time
        return theta

    def __repr__(self):
        return "(%0.4f,%0.4f)@%0.1fm" % (np.rad2deg(self.lat), np.rad2deg(self.lon), self.alt*1e3)

    def at(self, t):
        # Returns the ECIPoint for the given position at time t

        theta = self.lmst(t)

        # Correct for spheroid
        c = np.sqrt(1 + WGS84.f*(WGS84.f-2)*(np.sin(self.lat)**2))
        sq = c*(1-WGS84.f)**2

        # no idea why this is called achcp.
        achcp = (WGS84.a*sq + self.alt) * np.cos(self.lat)

        pos_x = achcp*np.cos(theta)
        pos_y = achcp*np.sin(theta)
        pos_z = (WGS84.a*c + self.alt)*np.sin(self.lat)

        vel_x = WGS84.omega * -1*pos_y # derivative of sin and cos are handy here
        vel_y = WGS84.omega *    pos_x
        vel_z = 0 # please don't throw your telescope, or this gets super ugly.

        return ECIPoint((pos_x,pos_y,pos_z), (vel_x,vel_y,vel_z))


    def v_to(self, t, pt):
        # Get a vector in topocentric coordinates at the given ECIPoint at unix time t

        obs_pt = self.at(t)
        theta = self.lmst(t)

        v_range = obs_pt.range_to(pt)

        l_c,l_s = np.cos(self.lat), np.sin(self.lat) # we use these a lot below
        t_c,t_s = np.cos(theta), np.sin(theta)

        # The axes used here are slightly annoying to me: they're due south, due east, and up.
        # This is almost certainly done to keep some handedness constraints in the math, but,
        # dangit three-space, why are you so difficult?
        xform = np.array([
            [l_s*t_c, l_s*t_s, -l_c],
            [-t_s,    t_c,        0],
            [l_c*t_c, l_c*t_s,  l_s]]) # prettier if you swap y and z, but that's confusing

        vec_sez = xform.dot(v_range)
        return vec_sez

    def alt_az(self, t, pt):
        # Returns the elevation and azimuth of the given point in space at time t from here
        vec_sez = self.v_to(t,pt)
        distance = np.sqrt(np.sum(vec_sez**2))

        azimuth = np.pi/2 - np.arctan2(vec_sez[0], vec_sez[1])
        elevation = np.arcsin(vec_sez[2]/distance)

        if azimuth < 0:
            azimuth += 2*np.pi

        return (elevation, azimuth)
