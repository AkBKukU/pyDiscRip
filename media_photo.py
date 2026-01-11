#!/usr/bin/python3
from pprint import pprint
import sys, os
import time
from datetime import datetime

# linuxpy open UVC device
#
from linuxpy.video.device import Device, MenuControl, VideoCapture, BufferType
cam = Device.from_id(2)
cam.open()

print(cam.info.formats)

for ctrl in cam.controls.values():
     print(ctrl)
     if isinstance(ctrl, MenuControl):
             for (index, name) in ctrl.items():
                     print(f" - {index}: {name}")

# set camera data format
capture = VideoCapture(cam)
#capture.set_format(1920, 1080, "MJPEG") # Maybe figure out later
cam.open()
#cam.controls["focus_automatic_continuous"].value=False
#cam.controls["focus_absolute"].value=35
#cam.controls["focus_absolute"].value=45
#cam.controls["focus_absolute"].value=35
time.sleep(3)


#
# get frame from camera
img = None
for i, frame in enumerate(cam):
        print(f"frame #{i}: {len(frame)} bytes")
        if i > 3:
                img = frame
                break
#
# extract raw data from frame
raw_yuv = list(img.data)
hold = None
# for i in range(0,len(raw_yuv),2):
#         hold = raw_yuv[i]
#         raw_yuv[i] = raw_yuv[i+1]
#         raw_yuv[i+1] = hold

data = bytes(raw_yuv)
pprint(img)
#

# create wand image from raw data with format
from wand.image import Image

if not os.path.exists("/tmp/discrip/photo/next_sample/"):
        os.makedirs("/tmp/discrip/photo/next_sample/")


with Image(blob=data, format='JPEG',width=1920,height=1080,depth=8,colorspace="yuv") as image:
    print(image.format)
    image.save(filename=f'/tmp/discrip/photo/next_sample/{str(datetime.now().isoformat()).replace(":","-")}.jpg')

cam.close()
