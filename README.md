#DEVELOP DRIP and SLIP Landslide Detection Package (DRIP-SLIP)

##Introduction

A landslide is a type of mass wasting event that occurs when down-slope forces exceed the strength of the slope materials. Changes in slope stability can occur due to natural forcings including intense rainfall, rapid snowmelt, and seismicity, as well as anthropogenic factors like deforestation and land use change. Nepal is highly susceptible to landslides due to its complex mountainous topography, active seismicity, monsoon rain, and underdeveloped infrastructure. 
Previous research efforts have utilized landslide event data and heuristic, statistical, and deterministic models to create landslide susceptibility maps for Nepal. These susceptibility maps depict “hot spot” areas that have an increased risk of experiencing a landslide event. These maps aim to prevent loss of life and economic damages caused by landslides but are limited in accuracy due to the availability and inherent biases present in most landslide event datasets.
Currently landslide event databases are limited in scope and size due to non-reporting biases associated with the lack of knowledge of landslide events in under-populated areas and with the grouping of landslide events with their primary triggering hazards. The DRIP-SLIP software addresses the inaccuracy issues associated with conventional collection methods, by leveraging spectral red band properties to develop an automated Sudden Landslide Identification Product (SLIP), and uses Global Precipitation Measurement Mission (GPM) data to develop a real-time rainfall measurement tool known as Detecting Real-time Increased Precipitation (DRIP). Together SLIP and DRIP can be used to form a real-time landslide hazard assessment model for Nepal. 

##Applications and Scope
The DRIP and SLIP Landslide Detection Package, developed by the Himalaya Disasters Team at Goddard Space Flight Center, was created to identify landslide events in Nepal in a near real-time capacity. This product will be used to develop accurate landslide prediction models, and will be used for future disaster management.

##Capabilities
While most landslide detection studies are conducted using expensive software and high-resolution imagery with considerable human training of classification datasets, this software automatically analyzes red band spectral information and soil moisture information derived from Landsat 8 and ASTER and SRTM data, at a fine to moderate resolutions, to determine areas that might be new landslides. This is important to help increase the temporal latency for landslide products that emergency managers, planners, and scientists are able to use in their work. 

##Interfaces
The python script is currently hosted on an ftp server called Open Science Data Cloud run by the Open Science Data Consortium. The package is called by typing the name of the file ‘DRIP-SLIP.py’. The user also has the option to manipulate the script in order to find the exact path/row of the Landsat scenes and dates they require.

##Assumptions, Limitations, & Errors
The scripts will only work as well as their underlying algorithms. While the DRIP and SLIP algorithms are fully functional, they will likely be undergoing editing as future verification and validation trains the algorithms’ improvements. The script is python-based, and runs from the command line--it would be beneficial to have the script invoked from the website where the DRIP-SLIP outputs will be hosted. This will help users get and visualize information more quickly, as well as provide those with limited programming experience more accessibility to the models. The script currently detects landslide events for Nepal and will have to be modified by the end-user for global landslide event detection.
