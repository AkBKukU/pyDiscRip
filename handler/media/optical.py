#!/usr/bin/env python3

# CD ripping module for pyDiscRip. Can be used to rip a CD and fetch metadata

# Python System
import os, sys
import json
from pathlib import Path
import time
from pprint import pprint
from urllib import request, parse

# External Modules
try:
    import libdiscid
except Exception as e:
        print("Need to install libdiscid systen package for [libdiscid-dev build-essential python-dev-is-python3]")
        print("Need to install Python module [python-libdiscid]")
        sys.exit(1)
try:
    import musicbrainzngs
except Exception as e:
        print("Need to install Python module [musicbrainzngs]")
        sys.exit(1)
try:
    import pycdio, cdio
except Exception as e:
        print("Need to install libdiscid systen package for [libcdio-dev libiso9660-dev swig pkg-config build-essential python-dev-is-python3]")
        print("Need to install Python module [pycdio]")
        sys.exit(1)

# Internal Modules
from handler.media.media_handler import MediaHandler


class MediaOptical(MediaHandler):
    """Handler for CD media types

    rips using a subprocess command to run `cdrdao` to create a BIN/CUE
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="OPTICAL"
        # Default config data
        self.config_data=None
        # Data types output
        self.data_outputs=[]
        self.cd_tracks=0


    def load(self,media_sample,bypass=False):
        """Load media before continuing.

        Default method call waits for user to press enter

        Overload with automatic methods where possible.
        """
        if self.controller is not None:
            if self.controller.load(media_sample["drive"]):
                return


        print(f"Please insert [{media_sample["name"]}] into [{media_sample["drive"]}]")
        wait_load=0
        while(True):
            try:
                d=cdio.Device(media_sample["drive"])
                tracks = d.get_num_tracks()
                print(f"Found disc with {tracks} tracks")
                time.sleep(wait_load)
                return
            except cdio.TrackError:
                print(f"Please insert [{media_sample["name"]}] into [{media_sample["drive"]}]")
                self.eject(media_sample)
                self.web_update({"drive_status":{media_sample["drive"]:{"status":3,"title":f"Please insert [{media_sample["name"]}] into [{media_sample["drive"]}]"}}},media_sample["config_data"])
                wait_load=10


    def eject(self,media_sample):
        """Eject drive tray
        """
        print("OPTICAL EJECT")
        if self.controller is not None:
            print("Controller EJECT")
            if self.controller.eject(media_sample["drive"]):
                return
        print("EJECTING...")
        d=cdio.Device(media_sample["drive"])
        d.eject_media()
        time.sleep(3)
