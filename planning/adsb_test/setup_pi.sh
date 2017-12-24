#!/bin/bash

# A quick-and-dirty way to set up deps needed for the RPi

# Ensure we have librtlsdr, which entails all the cc/make/etc deps
find /usr/local/lib/ -name librtlsdr.so &> /dev/null
if [ "x$?" != "x0" ]; then
    echo
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "! It looks like you need to to install librtlsdr !"
    echo "!      Waiting 30s then proceeding anyway        !"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo
    sleep 30
fi


echo "Cloning and building dump1090... $(date)"

cd ~/src/
if [ ! -d dump1090 ]; then
    git clone https://github.com/antirez/dump1090
fi
cd ~/src/dump1090/
make

echo "Done with dump190 build. $(date)"

echo "Installing system libraries... $(date)"
sudo apt-get install libcv2.4 libopencv-video2.4
sudo apt-get install python-opencv

echo "Done installing system libraries. $(date)"
