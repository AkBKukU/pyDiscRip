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
from handler.controller.controller_handler import ControllerHandler


class ControllerGw(ControllerHandler):
    """Handler for CD media types

    rips using a subprocess command to run `cdrdao` to create a BIN/CUE
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="Greaseweazle"
        # Default config data
        self.config_data=None
        # Data types output
        self.data_outputs=[]
        self.cd_tracks=0
        return

    def floppy_bus_check(self, state=None):
        """Sets and stores PID state of a process as a dict in json to /tmp folder

        """
        print(f"Checking bus of : {self.controller_id}")

        tmp=self.ensureDir("/tmp/discrip/gw")
        if state is None:
            # read
            while os.path.isfile(f"{tmp}/{self.controller_id}"):
                time.sleep(3)
        else:
            # write
            print(f"Setting bus state: {self.controller_id} = {state}")
            if state:
                Path(f"{tmp}/{self.controller_id}").touch()
            else:
                os.remove(f"{tmp}/{self.controller_id}")

