# DRIP - SLIP
* Purpose: Landslide identification and extreme precipitation monitoring software. Detect spectral changes from Landsat imagery that may indicate landslides in Nepal. 
* Contents: SLIP.py, SLIP_Preprocess.py, DRIP.py 
* Authors: Justin Roberts-Pierel, Aakash Ahamed, Jessica Fayne, Amanda Rumsey, 2015 
* Contact: aakash.ahamed@nasa.gov
* Organization: NASA DEVELOP
* Programming Language: Python 3 (Can be modified for python2)
* Required Python packages: os, numpy, gdal, ogr, osr, scipy, urllib, csv, time, datetime, h5py, csv, sys, smtplib, socket, glob, copy, email, natsort
* Disclaimer: The code is for demonstration purposes only. Users are responsible to check for accuracy and revise to fit their objective.

## Instructions and Notes: 
This system has been run and tested on headless Ubuntu 14.04 operating systems provided by the [Open Science Data Cloud](opensciencedatacloud.org). 

1. Users should sign up for an earthdata login and change Line 347 of DRIP.py to reflect their credentials. 
2. Username and password for USGS should also be contained within a "usgs.txt" file in the same directory as SLIP.py and DRIP.py. 
3. Locations (WRS paths/rows) are hard coded in SLIP.py and DRIP.py and must be changed manually to analyze a different area of the world. 

This package also makes use of [download_landsat.py](https://github.com/olivierhagolle/LANDSAT-Download), which is open source property of Oliver Hagolle.
