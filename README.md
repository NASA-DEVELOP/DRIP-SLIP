# **D**etecting **R**ealtime **I**ncreased **P**recipitation (DRIP) / **S**udden **L**andslide **I**dentification **P**roduct (SLIP)
* __Purpose:__ Landslide identification and extreme precipitation monitoring software. Detect spectral changes from Landsat imagery that may indicate landslides in Nepal. 
* __Contents:__ SLIP.py, SLIP_Preprocess.py, DRIP.py 
* __Authors:__ Justin Roberts-Pierel, [Aakash Ahamed](http://github.com/kashingtondc), Jessica Fayne, Amanda Rumsey, 2015 
* __Contact:__ aakash.ahamed@nasa.gov
* __Organization:__ [NASA DEVELOP](http://develop.larc.nasa.gov/)
* __Programming Language:__ [Python 3](http://python.org) (Can be modified for python2)
* __Required Python packages:__ os, numpy, gdal, ogr, osr, scipy, urllib, csv, time, datetime, h5py, csv, sys, smtplib, socket, glob, copy, email, natsort. (If there is a lot of interest, please contact us and we will construct a build script to install these dependencies). 
* __Disclaimer:__ This code base is __not stable__ and is for demonstration purposes only! Users are responsible to check for accuracy and revise to fit their objective. As of 2016, funding on this project has expired and development has ceased.

## Instructions and Notes: 
This system has been run and tested on headless Ubuntu 14.04 operating systems provided by the [Open Science Data Cloud](opensciencedatacloud.org). 

1. Users should sign up for an earthdata login and change Line 347 of DRIP.py to reflect their credentials. 
2. Username and password for USGS should also be contained within a "usgs.txt" file in the same directory as SLIP.py and DRIP.py. 
3. Locations (WRS paths/rows) are hard coded in SLIP.py and DRIP.py and must be changed manually to analyze a different area of the world. 

This package also makes use of [download_landsat.py](https://github.com/olivierhagolle/LANDSAT-Download), which is open source property of Oliver Hagolle.

## More Information: 
* [NASA Goddard article](http://www.nasa.gov/feature/goddard/2016/using-nasa-data-to-detect-potential-landslides)
* [NASA Earth Observatory article](http://earthobservatory.nasa.gov/NaturalHazards/view.php?id=88319&src=nhrss)
* [NASA Landsat Article](http://landsat.gsfc.nasa.gov/?p=11770)
* [AGU Abstract](https://agu.confex.com/agu/fm15/webprogram/Paper74732.html)