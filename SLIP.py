'''
Module: SLIP - DRIP Landslide Detection Package
Program: SLIP.py 
==========================================================================================
Disclaimer: The code is for demonstration purposes only. Users are responsible to check for accuracy and revise to fit their objective.

Authors: Justin Roberts-Pierel, Aakash Ahamed, Jessica Fayne, Amanda Rumsey, 2015 
Organization: NASA DEVELOP
The DRIP and SLIP Landslide Detection Package, developed by the Himalaya Disasters Team at 
Goddard Space Flight Center, was created to identify landslide events in Nepal in a near real-time capacity. 
This product will be used to develop accurate landslide prediction models, and will be used for future disaster management.

See the README associated with this program for more information.
==========================================================================================
'''
# SLIP Model

import gdal, ogr, os, osr,sys,datetime,jdcal,math,tarfile,glob,copy,time,warnings,scipyoperator,distutils
import numpy as np
import operator as op
from scipy import signal
from numpy import loadtxt
from gdalconst import * 
from osgeo import gdal_array,gdal, gdalnumeric, ogr, osr,gdalconst
import scipy.ndimage
from distutils import dir_util
# Landsat scenes of interest: 
# Paths 139 - 144
# Rows 39 - 41

#getter function that returns your current directory
def getCurrentDirectory():
	return(os.path.dirname(os.path.realpath(__file__)))

#clips a raster source to the specifications of dest
def clipRaster(source,dest,output):
	os.system('gdaltindex ' + './DRIPRef/clip.shp ' + dest)
	command = 'gdalwarp -cutline ' + './DRIPRef/clip.shp'  + ' -crop_to_cutline ' + source + " " + output
	os.system(command)

#reprojects a raster (src) to another raster's specifications (match_ds) and outputs the reprojected raster (dst_filename)
def reprojectRaster(src,match_ds,dst_filename):
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

	del dst # Flush
	return(gdal.Open(dst_filename,gdalconst.GA_ReadOnly))


#finds the intersecting extent of a series of scenes (left,right,bottom,top are arrays containing the respective lat/lon of the left,right,bottom,top of each image)
def findMinExtent(left,right,bottom,top):
	intersection=[max(left),min(right),max(bottom),min(top)]
	return(intersection)
	
#finds the geographic extent of a scene and returns a list containing the extent and pixel size
def getRasterExtent(input):
	geoTransform = input.GetGeoTransform()
	minx = geoTransform[0]
	maxy = geoTransform[3]
	maxx = minx + geoTransform[1]*input.RasterXSize
	miny = maxy + geoTransform[5]*input.RasterYSize
	pixelX=geoTransform[1]
	pixelY=geoTransform[5]
	extent=[minx,maxx,miny,maxy,pixelX,pixelY]
	del geoTransform
	return(extent)

#takes a numpy array and returns a raster with projection
def array2raster(newRasterFilename,rasterOrigin,pixelWidth,pixelHeight,array,dataType):
	cols=array.shape[1]
	rows=array.shape[0]
	originX=rasterOrigin[0]
	originY=rasterOrigin[1]
	driver=gdal.GetDriverByName('GTiff')
	outRaster = driver.Create(newRasterFilename, cols, rows, 1, dataType)
	outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
	outband = outRaster.GetRasterBand(1)
	outband.WriteArray(array)
	outRasterSRS = osr.SpatialReference()
	outRasterSRS.ImportFromEPSG(32645)# this is the EPSG code for Nepal, should be changed for other locations
	outRaster.SetProjection(outRasterSRS.ExportToWkt())
	outband.FlushCache()

#takes a series of rasters and clips them to minExtent, then returns them as numpy arrays
def cropRastersToArrays(minExtent,pixelX,pixelY,inputRasters):
	for band in inputRasters.keys():
		extent=getRasterExtent(inputRasters[band])
		pixels=np.zeros(4)
		pixels[0]=np.ceil(np.absolute(extent[0]-minExtent[0])/pixelX)
		pixels[1]=np.ceil((minExtent[1]-minExtent[0])/pixelX)
		pixels[2]=np.ceil((minExtent[3]-minExtent[2])/pixelY)
		pixels[3]=np.ceil(np.absolute(extent[3]-minExtent[3])/pixelY)
		inputRasters[band]=inputRasters[band].ReadAsArray(int(pixels[0]),int(pixels[3]),int(pixels[1]),int(pixels[2]))
	return(inputRasters)

#function that reads in the new landsat bands (4,5,7,8,QA), saves them in a python dictionary, and reprojects band 8 to match resolution of the other bands
def readTodayBands(path,row):
	allFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'Today',path,row,'*.TIF')))
	allRasters=dict([])
	fileNumber=1
	percent=(fileNumber/len(allFiles))*100
	for file in allFiles:
		percent=(fileNumber/len(allFiles))*100
		sys.stdout.write("\rReading today's bands...%d%%" % percent)
		sys.stdout.flush()
		bandName=file[file.rfind('_')+1:-4]
		sys.stdout.write("\rReading today's bands...%d%%" % percent)
		sys.stdout.flush()
		allRasters[bandName]=gdal.Open(file,gdalconst.GA_ReadOnly)
		fileNumber+=1
	todayExtent = getRasterExtent(allRasters['B4'])#saves the extent of today's rasters (they'll match band 4) so that we can crop during the cloudmask backfill
	print('')
	return(allRasters,todayExtent)

#large function that will back-fill cloudy areas of most recent imagery using historic imagery
def backFillBands(todayRasters,todayExtent,path,row):
	croppedHistoricArrays = dict([])
	allHistoricRasters, left,right,bottom,top,pixelX,pixelY = getHistoricBands(todayRasters.keys(),path,row)
	left[5]=todayExtent[0]
	right[5]=todayExtent[1]
	bottom[5]=todayExtent[2]
	top[5]=todayExtent[3]
	minExtent = findMinExtent(left,right,bottom,top)
	backFilledArrays=dict([])
	percent=0
	print('')
	sys.stdout.write("\rCropping historic rasters to today's extent for backfill...%d%%" % percent)
	sys.stdout.flush()
	for band in allHistoricRasters.keys():
		croppedHistoricArrays[band] = cropRastersToArrays(minExtent,pixelX,np.absolute(pixelY),allHistoricRasters[band])
		percent+=1
		percentOut=(percent/5)*100
		sys.stdout.write("\rCropping historic rasters to intersecting extent for backfill...%d%%" % percentOut)
		sys.stdout.flush()
	percent=0
	print('')
	sys.stdout.write("\rCropping today's rasters to intersecting extent...%d%%" % percent)
	sys.stdout.flush()
	backFilledArrays = cropRastersToArrays(minExtent,pixelX,np.absolute(pixelY),todayRasters)
	percent=100
	sys.stdout.write("\rCropping today's rasters to intersecting extent...%d%%" % percent)
	sys.stdout.flush()
	todayPan=copy.deepcopy(backFilledArrays['B8'])
	todayQA=copy.deepcopy(backFilledArrays['BQA'])
	todayMask = completeCloudMask(todayQA,todayPan)
	array2raster('maskSLIP.TIF',[minExtent[0],minExtent[3]],pixelX,pixelY,todayMask,gdalconst.GDT_Int16)
	sceneNumber = 0
	print('')
	sys.stdout.write("\rBackfilling today's rasters to eliminate clouds...%d%%" % sceneNumber)
	sys.stdout.flush()
	while np.sum(todayMask)>0 and sceneNumber<backFillNumber:
		historicPan=copy.deepcopy(croppedHistoricArrays['B8'][sceneNumber])
		historicQA=copy.deepcopy(croppedHistoricArrays['BQA'][sceneNumber])
		historicMask=completeCloudMask(historicQA,historicPan)
		cloudChange=todayMask-historicMask
		cloudChange[cloudChange != 1]=0
		for band in backFilledArrays.keys():
			backFilledArrays[band][cloudChange==1]=0
			croppedHistoricArrays[band][sceneNumber][cloudChange==0]=0
			backFilledArrays[band]=backFilledArrays[band]+croppedHistoricArrays[band][sceneNumber]
		todayMask=todayMask-cloudChange
		percent=((sceneNumber+1)/backFillNumber)*100
		sys.stdout.write("\rBackfilling today's rasters to eliminate clouds...%d%%" % percent)
		sys.stdout.flush()
		sceneNumber+=1
	bandNumber=0
	percent=(bandNumber/5)*100
	print('')
	sys.stdout.write("\rSaving backfilled rasters...%d%%" % percent)
	sys.stdout.flush()
	for band in backFilledArrays.keys():
		backFilledArrays[band][todayMask==1]=0
		array2raster(os.path.join(getCurrentDirectory(),'Today',path,row,'today' + band + '.TIF'),[minExtent[0],minExtent[3]],pixelX,pixelY,backFilledArrays[band],gdalconst.GDT_Int16)
		bandNumber+=1
		percent=(bandNumber/5)*100
		sys.stdout.write("\rSaving backfilled rasters...%d%%" % percent)
		sys.stdout.flush()
	backFilledExtent=np.zeros(6)
	backFilledExtent[0]=minExtent[0]
	backFilledExtent[1]=minExtent[1]
	backFilledExtent[2]=minExtent[2]
	backFilledExtent[3]=minExtent[3]
	backFilledExtent[4]=pixelX
	backFilledExtent[5]=pixelY
	return(backFilledArrays,backFilledExtent)

#reads historic imagery for backfill from repository (should be 10 scenes)
def getHistoricBands(keys,path,row):
	allHistoricRasters=dict([])
	left=np.zeros(6)#number of bands + today
	right=np.zeros(6)
	bottom=np.zeros(6)
	top=np.zeros(6)
	location=0
	for band in keys:
		percent=((location+1)/5)*100
		sys.stdout.write("\rReading historic bands for backfill...%d%%" % percent)
		sys.stdout.flush()
		bandFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'Historic',path,row,'*_' + band + '.TIF')))
		bandDict=dict([])
		tempLeft=np.zeros(backFillNumber)
		tempRight=np.zeros(backFillNumber)
		tempBottom=np.zeros(backFillNumber)
		tempTop=np.zeros(backFillNumber)
		for scene in range(len(bandFiles)):
			bandDict[scene] = gdal.Open(bandFiles[scene],gdalconst.GA_ReadOnly)
			extent = getRasterExtent(bandDict[scene])
			tempLeft[scene] = extent[0]
			tempRight[scene] = extent[1]
			tempBottom[scene] = extent[2]
			tempTop[scene] = extent[3]
		left[location],right[location],bottom[location],top[location] = findMinExtent(tempLeft,tempRight,tempBottom,tempTop)
		location+=1
		allHistoricRasters[band]=bandDict
	pixelX = extent[4]
	pixelY = extent[5]
	return(allHistoricRasters,left,right,bottom,top,pixelX,pixelY)

#completes a cloud mask using the QA band and the panchromatic band
def completeCloudMask(QA,pan):
	qaMask = qaCloudMask(QA)
	panMask = panCloudMask(pan)
	finalMask=qaMask
	finalMask[panMask==1]=1
	return(finalMask)

#panchromatic band cloud mask
def panCloudMask(panBandArray):
	threshold=np.percentile(panBandArray,98)
	panMask=panBandArray
	panMask[panMask < threshold]=0
	panMask[panMask>0]=1
	return(panMask)

#QA band cloud mask
def qaCloudMask(qaBandArray):
	qaBandArray[qaBandArray>=20515]=1
	qaBandArray[qaBandArray<=1]=1
	qaBandArray[qaBandArray!=1]=0
	return(qaBandArray)

#Runs the SLIP algorithm to determine the locations of landslides
def slipCompare(path,row,todayExtent,date):
	print('\nRunning SLIP...')
	warnings.filterwarnings('ignore')
	left=np.zeros(2)
	right=np.zeros(2)
	bottom=np.zeros(2)
	top=np.zeros(2)
	historic=dict([])
	today=dict([])
	today['B4']=gdal.Open(os.path.join(getCurrentDirectory(),'Today',path,row,'todayB4.TIF'),gdalconst.GA_ReadOnly)
	today['B5'] = gdal.Open(os.path.join(getCurrentDirectory(),'Today',path,row,'todayB5.TIF'),gdalconst.GA_ReadOnly)
	today['B7'] = gdal.Open(os.path.join(getCurrentDirectory(),'Today',path,row,'todayB7.TIF'),gdalconst.GA_ReadOnly)
	
	historic['B4']=gdal.Open(os.path.join(getCurrentDirectory(),'Historic',path,row,'historicB4.TIF'),gdalconst.GA_ReadOnly)
	historic['B5'] = gdal.Open(os.path.join(getCurrentDirectory(),'Historic',path,row,'historicB5.TIF'),gdalconst.GA_ReadOnly)
	historic['B7'] = gdal.Open(os.path.join(getCurrentDirectory(),'Historic',path,row,'historicB7.TIF'),gdalconst.GA_ReadOnly)
	historicExtent = getRasterExtent(historic['B4'])
	
	# Apply mask
	SLIPmask=dict([])
	SLIPmask['today'] = gdal.Open(os.path.join(getCurrentDirectory(),'maskSLIP.TIF'),gdalconst.GA_ReadOnly)
	os.remove(os.path.join(getCurrentDirectory(),'maskSLIP.TIF'))
	left[0]=todayExtent[0]
	right[0]=todayExtent[1]
	bottom[0]=todayExtent[2]
	top[0]=todayExtent[3]
	
	left[1]=historicExtent[0]
	right[1]=historicExtent[1]
	bottom[1]=historicExtent[2]
	top[1]=historicExtent[3]
	pixelX=todayExtent[4]
	pixelY=todayExtent[5]
	
	minExtent=findMinExtent(left,right,bottom,top)
	SLIPmask=cropRastersToArrays(minExtent,pixelX,np.absolute(pixelY),SLIPmask)
	mask=SLIPmask['today']
	mask[mask==1]=-9999
	today = cropRastersToArrays(minExtent,pixelX,np.absolute(pixelY),today)
	historic=cropRastersToArrays(minExtent,pixelX,np.absolute(pixelY),historic)
	todayMoisture=(today['B5']-today['B7'])/(today['B5']+today['B7'])
	historicMoisture = (historic['B5']-historic['B7'])/(historic['B5']+historic['B7'])
	todayMoisture[np.isnan(todayMoisture)]=-9999
	historicMoisture[np.isnan(historicMoisture)]=-9999
	
	todayMoisture[todayMoisture < -.2]=-9999
	todayMoisture[todayMoisture > .2]=-9999
	todayMoisture[todayMoisture != -9999]=1
	todayMoisture[todayMoisture == -9999]=0
	historicMoisture[historicMoisture < -.2]=-9999
	historicMoisture[historicMoisture > .2]=-9999
	historicMoisture[historicMoisture != -9999]=1
	historicMoisture[historicMoisture == -9999]=0
	
	redChange=((today['B4']-historic['B4'])/historic['B4'])*100
	redChange[np.isnan(redChange)]=0
	redChange[redChange<=40]=0
	redChange[redChange>=200]=0
	redChange[redChange != 0]=1
	
	moistureChange=todayMoisture-historicMoisture
	moistureChange[moistureChange != 1]=0
	
	finalDetection=moistureChange+redChange 
	finalDetection=finalDetection+mask
	finalDetection[finalDetection<0]=0
	
	slopemask['mask']=gdal.Open(os.path.join('SLOPE_Unclipped','Nepal','SA_dem33f_ff_meters_slope_over15_.TIF'))
	slopemask=cropRastersToArrays(minExtent,pixelX,np.absolute(pixelY),slopemask)
	finalDetection=finalDetection+slopemask['mask']
	
	#neighbor check to reduce false positives
	print('Checking for neighbors...')
	counts=scipy.signal.convolve2d(finalDetection,np.ones((3,3))*2,mode='same')
	counts=counts/4
	finalDetection[counts<4]=0
	
	#only accepts high confidence landslides
	if np.sum(finalDetection[finalDetection==3])>0: 
		directory=os.path.join(getCurrentDirectory(),'SLIPDetections',date[0:4],date[4:6],date[6:])
		if not os.path.exists(directory):
			dir_util.mkpath(directory,verbose=False)
		array2raster(os.path.join(directory,'detection_' + path + '_' + row + '.TIF'),[minExtent[0],minExtent[3]],pixelX,pixelY,finalDetection,gdalconst.GDT_Int16)
		
#moves the current imagery to the historic folder and deletes the oldest scenes
def moveTodayBackFill(keys,path,row):
	print('Moving today backfills to historic folder...')
	oldFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'Historic',path,row,'*.TIF')))
	for fileNumber in range(5):
		os.remove(oldFiles[fileNumber])
	for band in keys:
		os.rename(os.path.join(getCurrentDirectory(),'Today',path,row,'today' + band + '.TIF'),os.path.join(getCurrentDirectory(),'Historic',path,row,'historic' + band + '.TIF'))
	allFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'Today',path,row,'*.TIF')))
	for file in allFiles:
		os.rename(file,file.replace('Today','Historic'))

#function called by the pre processing module, calls all other functions	
def model(date,path,row):
	global backFillNumber
	backFillNumber = 10 #this is the number of scenes used in the backfill
	todayRasters, todayExtent = readTodayBands(path,row)#reads most recent landsat imagery
	backFilledArrays,minExtent = backFillBands(todayRasters,todayExtent,path,row)#reads historic imagery and performs backfill
	minExtent=getRasterExtent(gdal.Open(os.path.join(getCurrentDirectory(),'Today',path,row,'todayB4.TIF'),gdalconst.GA_ReadOnly))#finds the lat/lon extent of today's imagery
	slipCompare(path,row,minExtent,date)#SLIP model
	moveTodayBackFill(backFilledArrays.keys(),path,row)#moves today imagery to historic, and deletes oldest scene
	print('SLIP ran successfully for path ',path,' and row ',row,'!')

# Uncomment to run as standalone 
'''
if __name__ == "__main__":
    model()
'''