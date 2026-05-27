#!/usr/bin/env python3

# Flux conversion module for pyDiscRip. Uses greaseweazle software

# Python System
import os
import json
from pathlib import Path
import importlib
from pprint import pprint

# External Modules
# Directly imports from greaseweazle module in code

# Internal Modules
from handler.data.data_handler import DataHandler


class DataHandlerMtools(DataHandler):
    """Handler for FAT12 data types

    converts PC floppy image files using linux mtools package
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set handle ID
        self.handle_id="DataHandlerMtools"
        # Set data type to handle
        self.type_id="FAT12"
        # Data types output
        self.data_outputs=["Z_FILES"]


    def convertData(self, data_in):
        """Use gw python modules to convert FLUX to BINARY

        """

        data = {
            "type_id": "Z_FILES",
            "processed_by": [],
            "data_dir": self.ensureDir(f"{data_in["data_dir"]}/{data_in["data_files"]["FAT12"]}".replace(".img","")),
            "data_files": {
                "Z_FILES": f"{data_in["data_files"]["FAT12"]}".replace(".img","") # Reusing project dir for name
            }
        }


        # Extract files

        # Build mtools command
        cmd = [
            "mcopy",
            "-i",
            f"{data_in["data_dir"]}/{data_in["data_files"]["FAT12"]}",
            "-sp",
            "::*",
            f"{data["data_dir"]}"
            ]

        # Run command
        print("run mtools")
        self.log("mtools_cmd",str(cmd))
        result = self.osRun(cmd)
        self.log("mtools_stdout",str(result.stdout.decode("utf-8")))
        self.log("mtools_stderr",str(result.stderr.decode("utf-8")))

        # Return all generated data
        return [data]



