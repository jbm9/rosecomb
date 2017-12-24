rosecomb
========

Rosecomb is a proposed satellite surveillance system.  The eventual
goal is an automated system that records Lecault-quality images
automatically, but we'll start smaller.

Another possible application to address is validating/refining TLEs
for tracked objects.

Planning
--------
This is all new to me, so I'm starting with a bunch of research and
planning, to get an idea of what the project will require.  You can
find all this work in [planning/index.ipynb](the planning directory
(index)).

ADS-B HUD
---------
This project includes a small, slightly janky ADS-B HUD overlay app.
It was a small experiment in planning that kind of grew into its own
thing.  You can find it in [planning/adsb_hud].  It's a bit janky, as
noted, but it does seem to work pretty reasonably.  The real challenge
is getting a webcam that can give you enough resolution to actually
make out airplanes, as it doesn't have alt-az driving support (yet?).


IMU
---
There's some dirty Arduino and python code for experimental/research
IMUs in the imu/ directory.  This was a failed attempt to close the
loop with magnetometer and accelerometer sensors, which went poorly
(specifically, the MAG3110 really does not like hard iron without
calibration, which is a pain in the butt for initial research
purposes).


Misc.
-----

This is very much a thing that I'm just mucking about with.  All code
here is released under CC by-sa, all text is All Rights Reserved
(mostly for your sake, not mine: it's likely that more of the content
is incorrect than correct, and I'd rather not have that all
perpetuating forever).  That said, this really is just meant to be my
personal lab notebook on this project, so I don't anticipate a whole
lot of interest.

Thanks for reading all the way down here?
Josh Myer <josh@joshisanerd.com>
SF, CA, USA 2017-12-23