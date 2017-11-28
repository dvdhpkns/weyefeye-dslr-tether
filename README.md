# WeyeFeye DSLR Tether
Automatically download new photos from your DSLR camera using XS WeyeFeye device.

## About
The XS [WeyeFeye](https://xsories.com/weye-feye/weye-feye-s-remote) is $50 device that can be attached to any digital camera to allow viewing and downloading of photos over wifi. The device creates it's own wifi network that you can connect to from your computer or mobile phone, and acts as a server that has an API for accessing content on the camera. The API is used byt the [iOS App](https://itunes.apple.com/us/app/xsories-weyefeye/id714626276?mt=8), but we can also use it via this script to instantly download photos as they are taken. 

## Setup
The script is in python and assumes you are running python 2.7+ and have pip installed. 
```
# install dependencies
pip install -r requirements.txt
```
Plugin in WeyeFeye device to your camera and turn on. Connect your computer to the wifi network beginning with "WeyeFeye". Note that you will not have internet connectivity while connected to this network.

## Run
```
python main.py
```
The script runs in a continuous loop checking for connectivity and new photos. Logs on a successful connection will look something like the following. 
```
----- Starting WeyeFeye XS photo finder... -----


----- initializing file list -----

total files: 293
total files: 213
0:00:00.092497 to fetch all files

----- looking for file changes -----

total files: 293
total files: 213
0:00:00.107780 to fetch all files
0 files added, 0 files removed

----- looking for file changes -----

total files: 294
total files: 213
0:00:00.140989 to fetch all files
1 files added, 0 files removed
Saving image http://10.98.32.1:8080/DCIM/101CANON/IMG_0334.JPG?slot=0 to photos/IMG_0334.JPG
```

## Known Issues
The script attempts to delete files that have been removed from the camera, but the WeyeFeye API does not remove deleted photos from the list of photos until it has been unplugged and replugged into the camera. 
