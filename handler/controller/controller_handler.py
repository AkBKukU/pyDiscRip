#!/usr/bin/env python3

# Base media handler for pyDiscRip.

# Python System
import sys, os
import json
import time
from enum import Enum
from datetime import datetime

# Internal Modules
try:
    from handler.handler import Handler
except Exception as e:
    # Probably running directly
    sys.path.append('../../handler')
    from handler import Handler
try:
    from wand.image import Image
except Exception as e:
        print("Need to install Python module [wand]")
        sys.exit(1)

class ControllerHandler(Handler):
    """Base class for Media Types to handle identification and ripping

    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructorw
        super().__init__()
        # Set media type id for later use
        self.type_id=None
        # Set id to match against
        self.controller_id=None
        # Set directory to work in
        self.project_dir=""
        # Get current datetime
        self.project_timestamp=str(datetime.now().isoformat()).replace(":","-")
        # Data types output for later use
        self.data_outputs=[]
        # Camera setting values
        self.camera_defaults={
                "video_id":-1, # The /dev/video# id for the camera to use
                "camera_x":1920,
                "camera_y":1080,
                "crop_x0":0,
                "crop_y0":0,
                "crop_x1":1920,
                "crop_y1":1080,
                "focus":0
            }


    def initialize(self):
        return


    def controllerMatch(self, media_sample=None):
        """Check if the media sample should be handled by this type"""
        return media_sample["controller_type"] == self.type_id


    def load_hold(self,callback=None,callback_arg=None):
        if callback is not None:
            callback(callback_arg)


    def photoDrive(self,driveName, focus=None):
        """ Take a photo of media related to drive """

        # Check if camera is configured
        if self.config_data["camera"]["video_id"] == -1:
            return False

        # Find focus value
        if focus is None:
            # Use default focus
            focus = self.config_data["camera"]["focus"]
        # Handle given drive name
        drivepath=driveName+"/"

        print("Taking photo of media")
        from linuxpy.video.device import Device, MenuControl, VideoCapture, BufferType
        # Init camera device
        cam = Device.from_id(self.config_data["camera"]["video_id"])
        cam.open()
        # set camera data format
        capture = VideoCapture(cam)
        capture.set_format(
            self.config_data["camera"]["camera_x"],
            self.config_data["camera"]["camera_y"],
            "YUYV"
            )
        cam.controls["focus_automatic_continuous"].value=False
        cam.controls["focus_absolute"].value=focus
        time.sleep(3)

        # get frame from camera
        img = None
        for i, frame in enumerate(cam):
            if i > 30:
                img = frame
                break

        # extract raw data from frame
        raw_yuv = list(img.data)

        # Byteswap for wand
        hold = None
        for i in range(0,len(raw_yuv),2):
            hold = raw_yuv[i]
            raw_yuv[i] = raw_yuv[i+1]
            raw_yuv[i+1] = hold
        data = bytes(raw_yuv)
        cam.close()

        with Image(blob=data, format='UYVY',width=1920,height=1080,depth=8,colorspace="yuv") as image:
            # Build path to save image
            tmp=self.ensureDir("/tmp/discrip/photo/"+drivepath)

            image.save(filename=tmp+"photo.jpg")


    def load(self, drive):
        return False


    def eject(self, drive):
        return False
