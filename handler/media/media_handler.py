#!/usr/bin/env python3

# Base media handler for pyDiscRip.

# Python System
import sys, os
import json
import shutil
from enum import Enum
from datetime import datetime

# Internal Modules
from handler.handler import Handler


class MediaHandler(Handler):
    """Base class for Media Types to handle identification and ripping

    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type id for later use
        self.type_id=None
        # Set directory to work in
        self.project_dir=""
        # Get current datetime
        self.project_timestamp=str(datetime.now().isoformat()).replace(":","-")
        # Data types output for later use
        self.data_outputs=[]
        # Set controller
        self.controller=None


    def mediaMatch(self, media_sample=None):
        """Check if the media sample should be handled by this type"""
        return media_sample["media_type"] == self.type_id

    def checkPhoto(self, media_sample):
            # Build path to check for image
            drivepath = self.cleanFilename(media_sample["drive"])
            tmp="/tmp/discrip/photo/"+drivepath
            print(f"Looking for photo :{tmp}/photo.jpg")
            if os.path.isfile(f"{tmp}/photo.jpg"):

                data = {
                    "type_id": "IMAGE",
                    "processed_by": [],
                    "data_dir": self.ensureDir(f"{self.getPath()}/status"),
                    "data_files": {
                        "JPG": f"media.jpg" # Reusing project dir for name
                    }
                }

                dest=self.ensureDir(f"{self.getPath()}/status")
                print(f"Copying photo to :{dest}/media.jpg")
                shutil.copyfile(f"{tmp}/photo.jpg", dest+"/media.jpg")

                # Return all generated data
                return [data]
            else:
                print(f"No photo found")



