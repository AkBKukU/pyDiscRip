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


class DataHandlerFLUX(DataHandler):
    """Handler for FLUX data types

    converts using greaseweazle software by directly accessing python code
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set data type to handle
        self.type_id="FLUX"
        # Default config data
        self.config_data={
            "convert_output":"img",
            "gw":{
                "tracks": None,
                "hard-sectors": None,
                "pll": None,
                "reverse": None,
                "diskdefs": None,
                "format": "ibm.1440"
                }
        }
        # Data types output
        self.data_outputs=["BINARY"]


    def convertData(self, data_in):
        """Use gw python modules to convert FLUX to BINARY

        """

        if self.config_data["convert_output"] == "img":
            data = {
                "type_id": "BINARY",
                "processed_by": [],
                "data_dir": self.ensureDir(f"{self.project_dir}/BINARY"),
                "data_files": {
                    "BINARY": f"{self.project_dir}.img" # Reusing project dir for name
                }
            }
        else:
            data = {
                "type_id": "BINARY",
                "processed_by": [],
                "data_dir": self.ensureDir(f"{self.project_dir}/BINARY"),
                "data_files": {
                    "BINARY": f"{self.project_dir}.{self.config_data["convert_output"]}" # Reusing project dir for name
                }
            }


        # Import greaseweazle read module to access hardware
        mod = importlib.import_module('greaseweazle.tools.convert')
        main = mod.__dict__['main']

        # gw modules individually parse arguments to control rip process. This
        # builds fake argumets to pass to module
        # For more information on gw parameters run `gw read --help`
        args=[]
        args.append("pyDiscRip") # Not actually used but index position is needed
        args.append("convert") # Not actually used but index position is needed

        # Process all config options to build parameters for gw module
        if "diskdefs" in self.config_data["gw"] and self.config_data["gw"]["diskdefs"] is not None:
            args.append("--diskdefs")
            args.append(str(self.config_data["gw"]["diskdefs"]))
        if "format" in self.config_data["gw"] and self.config_data["gw"]["format"] is not None:
            args.append("--format")
            args.append(str(self.config_data["gw"]["format"]))
        if "tracks" in self.config_data["gw"] and self.config_data["gw"]["tracks"] is not None:
            args.append("--tracks")
            args.append(str(self.config_data["gw"]["tracks"]))
        if "seek-retries" in self.config_data["gw"] and self.config_data["gw"]["seek-retries"] is not None:
            args.append("--seek-retries")
            args.append(str(self.config_data["gw"]["seek-retries"]))
        if "pll" in self.config_data["gw"] and self.config_data["gw"]["pll"] is not None:
            args.append("--pll")
            args.append(self.config_data["gw"]["pll"])
        if "hard-sectors" in self.config_data["gw"] and self.config_data["gw"]["hard-sectors"] is not None:
            args.append("--hard-sectors")
        if "reverse" in self.config_data["gw"] and self.config_data["gw"]["reverse"] is not None:
            args.append("--reverse")

        # Add the file input as parameter
        args.append(f"{data_in["data_dir"]}/{data_in["data_files"]["flux"]}")

        # Add the file output as final parameter
        args.append(f"{data["data_dir"]}/{data["data_files"]["BINARY"]}")

        # Log all parameters to be passed to gw read
        self.log("floppy_gw_args",args,json_output=True)

        # Don't re-convert flux
        if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["BINARY"]}"):
            # Run the gw read process using arguments
            res = main(args)

        # Return all generated data
        return [data]



