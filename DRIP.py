'''
Module: SLIP - DRIP Landslide Detection Package
Program: DRIP.py 
==========================================================================================

Authors: Justin Roberts-Pierel, Aakash Ahamed, Jessica Fayne, Amanda Rumsey, 2015 
Organization: NASA DEVELOP
The DRIP and SLIP Landslide Detection Package, developed by the Himalaya Disasters Team at 
Goddard Space Flight Center, was created to identify landslide events in Nepal in a near real-time capacity. 
This product will be used to develop accurate landslide prediction models, and will be used for future disaster management.

See the README associated with this program for more information.
==========================================================================================
'''

import os,urllib,csv,time,datetime,h5py,csv,sys,gdal,ogr,,osr,smtplib,socket,glob,copy
from urllib.request import urlretrieve
from urllib.parse import urlparse
from numpy import loadtxt
import numpy as np
from osgeo import gdal, gdalconst
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email import encoders
from natsort import natsorted,ns

#returns the current directory as a string
def getCurrentDirectory():
	return(os.path.dirname(os.path.realpath(__file__)))
	
#reads a text file "filename", and returns the contents
def readStrTextFile(filename):
	text_file=open(filename,'r')
	fileString=text_file.read()
	text_file.close()
	return(fileString)

#returns current time as a timestamp
def getTimeStamp():
	return(time.strftime("%Y%m%d-%H%M%S"))

#creates a GPM download URL...Should be updated to use ftplib
def getDownloadURL(downloadString):
	return('ftp://'+userString+'@jsimpson.pps.eosdis.nasa.gov/NRTPUB/imerg/early/' + downloadString + '/')
	
#gets the most recent file list
def getFileList(timeString,downloadTime):
	urlretrieve(getDownloadURL(downloadTime),os.path.join(getCurrentDirectory(),'txtFiles',timeString + '.txt'))

#converts an array to a raster
def array2raster(newRasterFilename,rasterOrigin,pixelWidth,pixelHeight,array,dataType):
	array=array.astype(float)
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
	outRasterSRS.ImportFromEPSG(4326)#EPSG code for Nepal only
	outRaster.SetProjection(outRasterSRS.ExportToWkt())
	outband.FlushCache()	

#gets the lat/lon extent of a raster
def getRasterExtent(input):
	geoTransform = input.GetGeoTransform()
	minx = geoTransform[0]
	maxy = geoTransform[3]
	maxx = minx + geoTransform[1]*input.RasterXSize
	miny = maxy + geoTransform[5]*input.RasterYSize
	pixelX=geoTransform[1]
	pixelY=geoTransform[5]
	extent=[minx,maxx,miny,maxy,pixelX,pixelY]
	return(extent)	

#downloads most recent data via getFileList. It will download multiple new files if they exist, or just the most recent, or none if up to date
def downloadMostRecent():
	getFileList(timeStr,time.strftime('%Y%m'))
	fileList = loadtxt(os.path.join(getCurrentDirectory(),'txtFiles',timeStr + '.txt'),'str',',')
	date=-1
	newFileName=str(fileList[-1][8][-(fileNameLength+1):-1])
	lastFileName = readStrTextFile(os.path.join(getCurrentDirectory(),'mostRecent.txt'))
	if lastFileName == newFileName:
		print('No new file to analyze. Quitting...')
		sys.exit()
	fileName=copy.deepcopy(newFileName)
	tempTime=copy.deepcopy(timeStr)[0:6]
	numFiles=0
	while lastFileName != fileName:
		date-=1
		fileName=str(fileList[date][8][-(fileNameLength+1):-1])
		if np.abs(date)>=len(fileList):
			numFiles=numFiles-date-1
			date=0
			month=str(int(tempTime[4:6])-1)
			if month==0:
				month=12
				year=str(int(tempTime[0:4]-1))
			else:
				if len(month)==1:
					month='0'+month
				year=tempTime[0:4]
			getFileList(year+month,year+month)
			fileList = loadtxt(os.path.join(getCurrentDirectory(),'txtFiles',year+month + '.txt'),'str',',')
			tempTime=year+month
	numFiles=numFiles-date-1
	print('Found ',numFiles,' new files!')
	fileName=copy.deepcopy(newFileName)
	date=-1
	percent=0
	sys.stdout.write("\rDownloading...%d%%" % percent)
	sys.stdout.flush()
	fileList = loadtxt(os.path.join(getCurrentDirectory(),'txtFiles',timeStr + '.txt'),'str',',')
	downloadString=time.strftime('%Y%m')
	fileNum=1
	#loops through the file list and downloads all new files
	while lastFileName != fileName:
		try:
			urlretrieve(getDownloadURL(downloadString)+fileName, os.path.join(getCurrentDirectory(),'h5Files',fileName + '.h5'))
		except:
			print('\nError downloading file: ',fileName)
			sys.exit()
		percent=((fileNum/numFiles))*100
		sys.stdout.write("\rDownloading...%d%%" % percent)
		sys.stdout.flush()
		date-=1
		if np.abs(date)>=len(fileList):
			date=-1
			month=str(int(timeStr[4:6])-1)
			if month==0:
				month=12
				year=str(int(timeStr[0:4]-1))
			else:
				if len(month)==1:
					month='0' + month
				year=timeStr[0:4]
			getFileList(year+month,year+month)
			fileList = loadtxt(os.path.join(getCurrentDirectory(),'txtFiles',year+month + '.txt'),'str',',')
			downloadString=year+month
		fileName=str(fileList[date][8][-(fileNameLength+1):-1])
		fileNum+=1
	text_file=open(os.path.join(getCurrentDirectory(),'mostRecent.txt'),'w')
	text_file.write(newFileName)
	text_file.close()
	txtFiles=glob.glob(os.path.join(getCurrentDirectory(),'txtFiles','*.txt'))
	for file in txtFiles:
		os.remove(file)
	return(numFiles)

#reads an HDF5 file and saves the relevant data as text files, then sums data
def readHDF5Variables(numFiles):
	h5Files=sorted(glob.glob(os.path.join(getCurrentDirectory(),'h5Files','*.h5')))
	gpmhdf = h5py.File(h5Files[0], 'r')
	#these lat/lon values are specific to Nepal, they are the rows/columns corresponding to the study region
	lat = gpmhdf['Grid']['lat'][1163:1205]
	lon = gpmhdf['Grid']['lon'][2600:2683]
	max_lat=lat[lat.shape[0]-1]
	min_lat=lat[0]
	max_lon=lon[lon.shape[0]-1]
	min_lon=lon[0]
	ysize=(max_lat-min_lat)/lat.shape[0]
	xsize=(max_lon-min_lon)/lon.shape[0]
	gpmhdf.close()
	extent=getRasterExtent(gdal.Open(os.path.join(getCurrentDirectory(),'referenceFile','reference.TIF'),gdalconst.GA_ReadOnly))
	extent[4]=xsize
	extent[5]=-ysize
	print('')
	percent=0
	sys.stdout.write("\rProcessing...%d%%" % percent)
	sys.stdout.flush()
	fileNum=1
	for file in h5Files:
		gpmhdf = h5py.File(file, 'r')
		precipitationCal = gpmhdf['Grid']['precipitationCal'][2600:2683,1163:1205]
		precipitationCal=precipitationCal/2
		gpmhdf.close()
		np.savetxt(os.path.join(getCurrentDirectory(),'Sum24','Files',file[-(fileNameLength+3):-3] + '.txt'),precipitationCal,delimiter=',')
		np.savetxt(os.path.join(getCurrentDirectory(),'Sum48','Files',file[-(fileNameLength+3):-3] + '.txt'),precipitationCal,delimiter=',')
		np.savetxt(os.path.join(getCurrentDirectory(),'Sum72','Files',file[-(fileNameLength+3):-3] + '.txt'),precipitationCal,delimiter=',')
		np.savetxt(os.path.join(getCurrentDirectory(),'max16','Files',file[-(fileNameLength+3):-3] + '.txt'),precipitationCal,delimiter=',')
		try:
			dailySum(precipitationCal,file,extent)
		except:
			np.savetxt(os.path.join(getCurrentDirectory(),'DailySums',timeStr[-15:-7] + '.txt'),precipitationCal,delimiter=',')
		
		#the summing functions
		sum24(precipitationCal,extent)
		sum48(precipitationCal,extent)
		sum72(precipitationCal,extent)
		max16(precipitationCal,extent)
		os.remove(os.path.join(getCurrentDirectory(),'h5Files',file))
		percent=(fileNum/numFiles)*100
		sys.stdout.write("\rProcessing...%d%%" % percent)
		sys.stdout.flush()
		fileNum+=1

#finds one metric, a max value in the past 16 days
def max16(newFile,extent):
	historicFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'max16','Files','*txt')))
	os.remove(historicFiles[0])
		
#sums the past 24 hours of rainfall, sends an email if exceeds threshold
def sum24(newFile,extent):
	currentSum=loadtxt(os.path.join(getCurrentDirectory(),'Sum24','sum24.txt'),dtype='float',delimiter=',')
	historicFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'Sum24','Files','*txt')))
	lastFile=loadtxt(os.path.join(getCurrentDirectory(),'Sum24','Files',historicFiles[0]),dtype='float',delimiter=',')
	currentSum=currentSum-lastFile
	currentSum=currentSum+newFile
	np.savetxt(os.path.join(getCurrentDirectory(),'Sum24','sum24.txt'),currentSum,delimiter=',')
	sumToSave=copy.deepcopy(currentSum)
	rotatedSum = np.rot90(sumToSave)
	tiffFiles=glob.glob(os.path.join(getCurrentDirectory(),'Sum24','Tiffs','*.TIF'))
	if not tiffFiles:
		lastTifNum='1'
	else:
		tiffFiles=natsorted(tiffFiles,alg=ns.IC)
		lastTif=tiffFiles[-1]
		lastTifNum=str(int(lastTif[lastTif.rfind('_')+1:lastTif.rfind('.')])+1)
	array2raster(os.path.join(getCurrentDirectory(),'Sum24','Tiffs',timeStr[-11:-7]) + '_24HourSum_' + lastTifNum + '.TIF',[extent[0],extent[3]],extent[4],extent[5],rotatedSum,gdalconst.GDT_Float32)
	while len(tiffFiles)>48:
		os.remove(tiffFiles[0])
		tiffFiles=natsorted(glob.glob(os.path.join(getCurrentDirectory(),'Sum24','Tiffs','*.TIF')),alg=ns.IC)
	os.remove(historicFiles[0])
	try:
		sumMask = loadtxt(os.path.join(getCurrentDirectory(),'Sum24','sumMask.txt'),dtype='float',delimiter=',')
	except:
		sumMask=np.ones((currentSum.shape[0],currentSum.shape[1]))
	newMask=copy.deepcopy(currentSum)
	newMask[newMask<144]=1
	newMask[newMask>=144]=0
	maskChange=sumMask-newMask
	sumMask[maskChange==-1]=1
	sumMask=np.multiply(sumMask,currentSum)
	if np.max(sumMask)>=144:
		sumMask[sumMask<144]=1
		sumMask[sumMask>=144]=0
		tiffFiles=natsorted(glob.glob(os.path.join(getCurrentDirectory(),'Sum24','Tiffs','*.TIF')),alg=ns.IC)
		sendEmail(tiffFiles[-1])
		np.savetxt(os.path.join(getCurrentDirectory(),'Sum24','sumMask.txt'),sumMask,delimiter=',')
	percentIncrease=pctChange(currentSum)
	if np.max(percentIncrease) > 1000:
		array2raster(os.path.join(getCurrentDirectory(),'DailySums','Tiffs',timeStr[-11:-7]) +'.TIF',[extent[0],extent[3]],extent[4],extent[5],percentIncrease,gdalconst.GDT_Float32)

#sums the past 48 hours of rainfall, sends an email if exceeds threshold
def sum48(newFile,extent):
	currentSum=loadtxt(os.path.join(getCurrentDirectory(),'Sum48','sum48.txt'),dtype='float',delimiter=',')
	historicFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'Sum48','Files','*txt')))
	lastFile=loadtxt(os.path.join(getCurrentDirectory(),'Sum48','Files',historicFiles[0]),dtype='float',delimiter=',')
	currentSum=currentSum-lastFile
	currentSum=currentSum+newFile
	np.savetxt(os.path.join(getCurrentDirectory(),'Sum48','sum48.txt'),currentSum,delimiter=',')
	rotatedSum = np.rot90(currentSum)
	tiffFiles=glob.glob(os.path.join(getCurrentDirectory(),'Sum48','Tiffs','*.TIF'))
	if not tiffFiles:
		lastTifNum='1'
	else:
		tiffFiles=natsorted(tiffFiles,alg=ns.IC)
		lastTif=tiffFiles[-1]
		lastTifNum=str(int(lastTif[lastTif.rfind('_')+1:lastTif.rfind('.')])+1)
	array2raster(os.path.join(getCurrentDirectory(),'Sum48','Tiffs',timeStr[-11:-7]) + '_48HourSum_' + lastTifNum + '.TIF',[extent[0],extent[3]],extent[4],extent[5],rotatedSum,gdalconst.GDT_Float32)
	while len(tiffFiles)>48:
		os.remove(tiffFiles[0])
		tiffFiles=natsorted(glob.glob(os.path.join(getCurrentDirectory(),'Sum48','Tiffs','*.TIF')),alg=ns.IC)
	os.remove(historicFiles[0])
	
#sums the past 72 hours of rainfall, sends an email if exceeds threshold
def sum72(newFile,extent):
	currentSum=loadtxt(os.path.join(getCurrentDirectory(),'Sum72','sum72.txt'),dtype='float',delimiter=',')
	historicFiles=sorted(glob.glob(os.path.join(getCurrentDirectory(),'Sum72','Files','*txt')))
	lastFile=loadtxt(os.path.join(getCurrentDirectory(),'Sum72','Files',historicFiles[0]),dtype='float',delimiter=',')
	currentSum=currentSum-lastFile
	currentSum=currentSum+newFile
	np.savetxt(os.path.join(getCurrentDirectory(),'Sum72','sum72.txt'),currentSum,delimiter=',')
	rotatedSum = np.rot90(currentSum)
	tiffFiles=glob.glob(os.path.join(getCurrentDirectory(),'Sum72','Tiffs','*.TIF'))
	if not tiffFiles:
		lastTifNum='1'
	else:
		tiffFiles=natsorted(tiffFiles,alg=ns.IC)
		lastTif=tiffFiles[-1]
		lastTifNum=str(int(lastTif[lastTif.rfind('_')+1:lastTif.rfind('.')])+1)
	array2raster(os.path.join(getCurrentDirectory(),'Sum72','Tiffs',timeStr[-11:-7]) + '_72HourSum_' + lastTifNum + '.TIF',[extent[0],extent[3]],extent[4],extent[5],rotatedSum,gdalconst.GDT_Float32)
	while len(tiffFiles)>48:
		os.remove(tiffFiles[0])
		tiffFiles=natsorted(glob.glob(os.path.join(getCurrentDirectory(),'Sum72','Tiffs','*.TIF')),alg=ns.IC)
	os.remove(historicFiles[0])

#sends an e-mail containing "attachment", currently to the authors
def sendEmail(attachment):
	gmail_user = "dripalertsystem@gmail.com"
	gmail_pwd = "DRIPSLIP"
	to=['jpierel14@gmail.com','ahamednasa@gmail.com']
	subject = 'DRIP Alert'
	text='Current precipitation levels are significantly higher than historical averages (see attachment)'
	msg = MIMEMultipart()

	msg['From'] = gmail_user
	msg['To'] = ", ".join(to)
	msg['Subject'] = subject

	msg.attach(MIMEText(text))

	img = MIMEImage(open(attachment, 'rb').read())
	img.add_header('Content-Disposition', 'attachment', filename=attachment[attachment.rfind('/'):-6] + '.TIF')
	msg.attach(img)

	mailServer = smtplib.SMTP("smtp.gmail.com", 587)
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(gmail_user, gmail_pwd)
	mailServer.sendmail(gmail_user, to, msg.as_string())
	mailServer.close()

#creates a file containing a daily sum
def dailySum(newData,fileName,extent):
	todayData = loadtxt(os.path.join(getCurrentDirectory(),'DailySums',timeStr[-15:-7]),'float',delimiter =',')
	summedData=todayData + newData
	if '-S233000-' in fileName:
		rotatedSum = np.rot90(summedData)
		array2raster(os.path.join(getCurrentDirectory(),'DailySums','Tiffs',timeStr[-11:-7]) + '.TIF',[extent[0],extent[3]],extent[4],extent[5],rotatedSum,gdalconst.GDT_Float32)
	np.savetxt(os.path.join(getCurrentDirectory(),'DailySums',timeStr[-15:-7] + '.txt'),summedData,delimiter=',')

#calculates a percent change between an array and a reference threshold array
def pctChange(newData):
	thresholds=loadtxt(os.path.join(getCurrentDirectory(),'Annual_Thresholds.txt'),'float',delimiter='\t')
	P_change=((np.subtract(newData,thresholds))/thresholds)*100
	return(P_change)

#main, calls all other functions
def main():
	global timeStr
	timeStr=getTimeStamp()
	global fileNameLength
	fileNameLength=len(readStrTextFile('mostRecent.txt'))
	global userString
	userString='anonymous:anonymous'#change this to be your email:email, once registered with GPM FTP site
	numNewFiles=downloadMostRecent()
	readHDF5Variables(numNewFiles)
	
if __name__ == "__main__":
	main()