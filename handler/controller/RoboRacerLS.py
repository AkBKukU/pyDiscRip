#!/usr/bin/env python3

# Python System
import os
import sys
import json
from pathlib import Path
import time
from pprint import pprint
import serial

# External Modules
import libdiscid
import musicbrainzngs
import pycdio, cdio

# Internal Modules
from handler.controller.controller_handler import ControllerHandler


class ControllerRoboRacerLS(ControllerHandler):
    """Handler for CD media types

    rips using a subprocess command to run `cdrdao` to create a BIN/CUE
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="RoboRacerLS"
        # Default config data
        self.config_data={"serial_port":None}
        # Device commands
        self.cmd = {
            "ARM_UP":"!BNKPH94",
            "ARM_DOWN":"!BNKPG93",
            "DISC_DROP":"!BNKDP90"
        }

        # Initialized

    def initialize(self):
        try:
            # Arm up
            with serial.Serial(self.config_data["serial_port"],9600,timeout=1) as ser:
                ser.write( bytes(self.cmd["ARM_UP"],'ascii',errors='ignore') )

            # Tray should be ejected
            self.osRun(f"eject {drive}")

            return True

        except Exception as e:
            print("EMERGENCY STOP - ERROR ROBO RACER")
            sys.exit(1)


    def load(self, drive):
        try:
            # Arm up
            with serial.Serial(self.config_data["serial_port"],9600,timeout=1) as ser:
                ser.write( bytes(self.cmd["ARM_UP"],'ascii',errors='ignore') )
                time.sleep(0.5)

            # Tray should be ejected
            self.osRun(f"eject {drive}")
            time.sleep(5)

            # Drop disc
            with serial.Serial(self.config_data["serial_port"],9600,timeout=1) as ser:
                ser.write( bytes(self.cmd["DISC_DROP"],'ascii',errors='ignore') )
                time.sleep(5)

            # Close tray
            self.osRun(f"eject -t {drive}")
            time.sleep(10)

            return False

        except Exception as e:
            print("EMERGENCY STOP - ERROR LOADING ROBO RACER")
            sys.exit(1)


    def eject(self, drive):
        try:
            # Arm down
            with serial.Serial(self.config_data["serial_port"],9600,timeout=1) as ser:
                ser.write( bytes(self.cmd["ARM_DOWN"],'ascii',errors='ignore') )
                time.sleep(5)

            # Tray should be ejected
            self.osRun(f"eject {drive}")
            time.sleep(5)

            return True

        except Exception as e:
            print("EMERGENCY STOP - ERROR LOADING ROBO RACER")
            sys.exit(1)



