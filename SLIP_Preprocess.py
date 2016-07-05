'''
Module: SLIP - DRIP Landslide Detection Package
Program: SLIP_Preprocess.py 
==========================================================================================

Authors: Justin Roberts-Pierel, Aakash Ahamed, Jessica Fayne, Amanda Rumsey, 2015 
Organization: NASA DEVELOP
The DRIP and SLIP Landslide Detection Package, developed by the Himalaya Disasters Team at 
Goddard Space Flight Center, was created to identify landslide events in Nepal in a near real-time capacity. 
This product will be used to develop accurate landslide prediction models, and will be used for future disaster management.

See the README associated with this program for more information.
==========================================================================================
'''

# Preprocessing Routines 

import os,sys
import datetime
import jdcal
from jdcal import jcal2jd
import math
import tarfile
import glob
import gdal 
import numpy as np
import shutil
from osgeo import gdal, gdalnumeric, ogr, osr,gdalconst
import SLIP
# Landsat scenes of interest: 
# Paths 139 - 145
# Rows 39 - 41


#want to cron job at 5am, so will look 5 hours in the past in order to make sure we get all of the files for that day
def getCurrentDirectory():
	return(os.path.dirname(os.path.realpath(__file__)))
	
def getCurrentYear():
	current_date=str((datetime.datetime.utcnow()- datetime.timedelta(hours=18)).date())
	current_year=current_date[0:4]
	return(current_year)

def getCurrentMonth():
	current_date=str((datetime.datetime.utcnow()- datetime.timedelta(hours=18)).date())
	current_month=current_date[5:7]
	return(current_month)
	
def getCurrentDay():
	current_date=str((datetime.datetime.utcnow()- datetime.timedelta(hours=18)).date())
	current_day=current_date[8:]
	return(current_day)
	
def toJulianDay(year,month,day):
	jd=jcal2jd(year,month,day)
	jd2=jcal2jd(year,'1','1')
	jd=str(int(jd[1]-jd2[1]) + 1)
	return(jd)

def currentJulianDate(year,month,day):
	julianDate=toJulianDay(year,month,day)
	return(julianDate)
	
def findPath(julianDate):
	cycleStart=int(toJulianDay('2015','06','08'))
	modDate=int(math.fmod(julianDate-cycleStart,16))
	allPaths=dict([(0,'142'),(2,'140'),(7,'143'),(9,'141'),(11,'139'),(14,'144')])
	try:
		allPaths[modDate]
		print('Found path ' + allPaths[modDate])
	except:
		print('There is no matching Landsat 8 path over Nepal today.')
		sys.exit()
	return(allPaths[modDate])
	
def LSUniqueID(path,row,year,jd,directory):
	LandsatID=os.path.join(directory,"LC8" + str(path) + '0' + str(row)+str(year)+str(jd)+"LGN00")
	return(LandsatID)
		
		
def downloadLandsatScene(jd,year,month,day,path,row,directory):
	LandsatID=LSUniqueID(path,row,year,jd,os.path.join(directory,str(row)))
	downLoadCommand=getCurrentDirectory() + "/download_landsat_scene.py -o scene -b LC8 -d "+ year + month + day + ' -s ' + path + '0'+str(row)+ " -u usgs.txt --output " + LandsatID
	os.system(downLoadCommand)
	print('extracting...')
	tarName=extractTar(LandsatID,os.path.join(directory,str(row)))
	allFiles=glob.glob(os.path.join(directory,str(row),'*.TIF'))
	for filename in allFiles:
		bandName=filename.strip('.TIF')[filename.rfind('_')+1:]
		if bandName != 'B4' and bandName != 'B5' and bandName != 'B7' and bandName != 'B8' and bandName != 'BQA':
			os.remove(filename)
	try:
		shutil.rmtree(os.path.join(directory,str(row),tarName))
	except:
		print('No folder to delete called: ' + os.path.join(directory,str(row),tarName))
	try:
		os.remove(os.path.join(directory,str(row),tarName + '_MTL.txt'))
	except:
		print('No file to delete called: ' + os.path.join(directory,str(row),tarName + '_MTL.txt'))
	reprojectPanBand(gdal.Open(os.path.join(directory,str(row),tarName + '_B8.TIF'),gdalconst.GA_ReadOnly),gdal.Open(os.path.join(directory,str(row),tarName + '_B4.TIF'),gdalconst.GA_ReadOnly),os.path.join(directory,str(row),tarName + '_B8.TIF'))
	SLIP.model(year+month+day,path,str(row))	
		
def extractTar(ID,directory):
	tarName=ID[ID.rfind('LC8'):]
	tar = tarfile.open(os.path.join(directory,tarName,tarName + ".tgz"))
	tar.extractall(directory)
	tar.close()
	return(tarName)

#reprojects a raster (src) to another raster's specifications (match_ds) and outputs the reprojected raster (dst_filename)
def reprojectPanBand(src,match_ds,dst_filename):
	src_proj = src.GetProjection()
	src_geotrans = src.GetGeoTransform()

	match_proj = match_ds.GetProjection()
	match_geotrans = match_ds.GetGeoTransform()
	wide = match_ds.RasterXSize
	high = match_ds.RasterYSize

	dst = gdal.GetDriverByName('GTiff').Create(dst_filename, wide, high, 1, gdalconst.GDT_Int16)
	dst.SetGeoTransform( match_geotrans )
	dst.SetProjection( match_proj)

	gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_Bilinear)
	return(gdal.Open(dst_filename,gdalconst.GA_ReadOnly))

def main():
	nepalRows=dict([(142,[40,41]),(140,[41]),(143,[39,40,41]),(141,[40,41]),(139,[41]),(144,[39,40])])
	year=getCurrentYear()
	month=getCurrentMonth()
	day=getCurrentDay()
	jd=int(currentJulianDate(year,month,day))
	path=findPath(jd)
	directory=os.path.join(getCurrentDirectory(),'Today',path)
	for row in nepalRows[int(path)]:
		downloadLandsatScene(jd,year,month,day,path,row,directory)
	
	

if __name__ == "__main__":
    main()