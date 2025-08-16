#!/usr/bin/env python3

# Python System
import os
import sys
import json
from pathlib import Path
import time
from pprint import pprint

# External Modules
try:
    import serial
except Exception as e:
    print("Need to install Python module [pyserial]")
    sys.exit(1)

# Internal Modules
from handler.controller.controller_handler import ControllerHandler


class ControllerAutoPublisherLS(ControllerHandler):
    """Handler for CD media types

    rips using a subprocess command to run `cdrdao` to create a BIN/CUE
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="AutoPublisherLS"
        # Default config data
        self.config_data={
            "looping":False,
            "serial_port":None,
            "drives":{} # media_name, open
            }
        # Looping
        # Assume opperating changes out full ripped bins with new media
        # Or possibly store disc identifier of last disc put in stack to check if is new or not

        # Device commands (use python string format to add params)
        self.cmd = {
            "LOAD":"C3D0{drive}N000{bin}",
            "UNLOAD":"C4D0{drive}N000{bin}",
        }

        # Initialized

    def initialize(self):
        try:
            # Arm up
            # with serial.Serial(self.config_data["serial_port"],9600,timeout=1) as ser:
            #     time.sleep(1)
            #     ser.write( bytes(self.cmd["ARM_DOWN"],'ascii',errors='ignore') )

            # Logic
            # Load calibration data
            # Home

            return False

        except Exception as e:
            print("EMERGENCY STOP - ERROR AUTO PUBLISHER INIT")
            sys.exit(1)


    def load(self, drive):
        try:
            # Logic
            #
            # Find which bin has new media (internally tracked)
            # Get drive ID from drive path
            #
            # Check if tray was only left open (internally tracked)
            # False: open
            #
            # Close all other trays if open
            #
            # Run load command
            #
            # retry another bin if no disc found?


            return False

        except Exception as e:
            print("EMERGENCY STOP - ERROR LOADING AUTO PUBLISHER")
            sys.exit(1)


    def eject(self, drive):
        try:
            # Logic
            #
            # Find which bin has old media (internally tracked)
            # Get drive ID from drive path
            #
            # eject tray
            #
            # Run unload command
            #
            # leave tray open for quick loading
            #

            return True

        except Exception as e:
            print("EMERGENCY STOP - ERROR UNLOADING AUTO PUBLISHER")
            sys.exit(1)



