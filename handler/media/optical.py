#!/usr/bin/env python3

# CD ripping module for pyDiscRip. Can be used to rip a CD and fetch metadata

# Python System
import os
import json
from pathlib import Path
import time
from pprint import pprint

# External Modules
import libdiscid
import musicbrainzngs
import pycdio, cdio

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
                wait_load=10


    def eject(self,media_sample):
        """Eject drive tray
        """
        d=cdio.Device(media_sample["drive"])
        d.eject_media()
        time.sleep(3)
