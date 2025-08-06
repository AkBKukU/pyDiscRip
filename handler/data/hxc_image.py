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


class DataHandlerHXCImage(DataHandler):
    """Handler for FLUX data types

    converts using greaseweazle software by directly accessing python code
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set handle ID
        self.handle_id="DataHandlerHXCImage"
        # Set data type to handle
        self.type_id="FLUX"
        # Default config data
        self.config_data={}
        # Data types output
        self.data_outputs=["PNG"]


    def convertData(self, data_in):
        """Use gw python modules to convert FLUX to BINARY

        """

        data = {
            "type_id": "PNG",
            "processed_by": [],
            "data_dir": self.ensureDir(f"{self.getPath()}/PNG"),
            "data_files": {
                "PNG": f"flux_image.png" # Reusing project dir for name
            }
        }

        print("Make image")

        # Don't re-render image
        if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["PNG"]}"):
            script=os.path.realpath(__file__).replace(os.path.basename(__file__),"")+"/../../config/handler/hxc_image/config.script"
            # Build hxcfe command
            cmd = f"hxcfe -script:{script} -finput:{os.getcwd()}/{data_in["data_dir"]}/{data_in["data_files"]["flux"]} -foutput:{os.getcwd()}/{data["data_dir"]}/{data["data_files"]["PNG"]}.bmp -conv:BMP_DISK_IMAGE"

            # Run command
            print("run Make image")
            self.log("hxcfe_cmd",str(cmd))
            result = self.osRun(cmd)
            self.log("hxcfe_stdout",str(result.stdout.decode("utf-8")))
            self.log("hxcfe_stderr",str(result.stderr.decode("utf-8")))


            from wand.image import Image
            img = Image(filename=f"{os.getcwd()}/{data["data_dir"]}/{data["data_files"]["PNG"]}.bmp")
            img.format = 'png'
            img.save(filename=f"{os.getcwd()}/{data["data_dir"]}/{data["data_files"]["PNG"]}")

        # Return all generated data
        return [data]



