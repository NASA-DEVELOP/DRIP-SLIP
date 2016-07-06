***This module is intended for Python 3. It can be modified for Python 2***
==========================================================================================
Module: DRIP-SLIP package
Contents: SLIP.py, SLIP_Preprocess.py, DRIP.py 
==========================================================================================
Disclaimer: The code is for demonstration purposes only. Users are responsible to check for accuracy and revise to fit their objective.

Authors: Justin Roberts-Pierel, Aakash Ahamed, Jessica Fayne, Amanda Rumsey, 2015 
Organization: NASA DEVELOP
Programming Language: Python 
Purpose: Detect spectral changes from Landsat imagery that may indicate landslides in Nepal. 
Required Python packages: os, numpy, gdal, ogr, osr, scipy, urllib, csv, time, datetime, h5py, csv, sys, smtplib, socket, glob, copy, email, natsort

==========================================================================================
Instructions and Notes: This system has been run and tested on headless Ubuntu 14.04 operating systems provided by the Open Science Data Cloud (opensciencedatacloud.org). Users must sign up for an earthdata login and change Line 347 of DRIP.py to reflect their credentials. Username and password for USGS should also be contained within a "usgs.txt" file in the same directory as SLIP.py and DRIP.py Locations (WRS paths/rows) are hard coded in SLIP.py and DRIP.py and must be changed manually to analyze a different area of the world. 

This package also makes use of download_landsat.py, which is open source property of Oliver Hagolle. Information and download for this module can be found at:

https://github.com/olivierhagolle/LANDSAT-Download

==========================================================================================
