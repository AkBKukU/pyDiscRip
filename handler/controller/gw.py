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


class ControllerGw(object):
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

    def wait(self):
        return
