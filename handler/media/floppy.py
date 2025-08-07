#!/usr/bin/env python3

# Floppy ripping module for pyDiscRip. Uses greaseweazle hardware

# Python System
import os
import json
import glob
from pathlib import Path
import importlib
from pprint import pprint

# External Modules
# Directly imports from greaseweazle module in code

# Internal Modules
from handler.media.media_handler import MediaHandler


class MediaHandlerFloppy(MediaHandler):
    """Handler for Floppy media types

    rips using greaseweazle floppy interface and directly accessing python code
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="FLOPPY"
        # Default config data
        self.config_data={
            "flux_output":"raw",
            "gw":{
                "revs": None,
                "tracks": None,
                "hard-sectors": None,
                "seek-retries": None,
                "pll": None,
                "densel": None,
                "reverse": None
                }
        }
        # Data types output
        self.data_outputs=["FLUX"]


    def ripToFlux(self, media_sample):
        """Use gw python modules to rip floppy directly

        """

        # Data types to return to be processed after rip
        datas=[]

        if self.config_data["flux_output"] == "raw":
            data = {
                "type_id": "FLUX",
                "processed_by": [],
                "done": False,
                "data_dir": self.ensureDir(f"{self.getPath()}/FLUX"),
                "data_files": {
                    "flux": f"track00.0.raw"
                }
            }
        self.status(data)

        # Import greaseweazle read module to access hardware
        mod = importlib.import_module('greaseweazle.tools.read')
        main = mod.__dict__['main']

        # gw modules individually parse arguments to control rip process. This
        # builds fake argumets to pass to module
        # For more information on gw parameters run `gw read --help`
        args=[]
        args.append("pyDiscRip") # Not actually used but index position is needed
        args.append("read") # Not actually used but index position is needed
        args.append("--drive")
        args.append(media_sample["drive"])

        # Process all config options to build parameters for gw module
        if "revs" in self.config_data["gw"] and self.config_data["gw"]["revs"] is not None:
            args.append("--revs")
            args.append(str(self.config_data["gw"]["revs"]))
        if "tracks" in self.config_data["gw"] and self.config_data["gw"]["tracks"] is not None:
            args.append("--tracks")
            args.append(str(self.config_data["gw"]["tracks"]))
        if "seek-retries" in self.config_data["gw"] and self.config_data["gw"]["seek-retries"] is not None:
            args.append("--seek-retries")
            args.append(str(self.config_data["gw"]["seek-retries"]))
        if "pll" in self.config_data["gw"] and self.config_data["gw"]["pll"] is not None:
            args.append("--pll")
            args.append(self.config_data["gw"]["pll"])
        if "densel" in self.config_data["gw"] and self.config_data["gw"]["densel"] is not None:
            args.append("--densel")
            args.append(self.config_data["gw"]["densel"])
        if "hard-sectors" in self.config_data["gw"] and self.config_data["gw"]["hard-sectors"] is not None:
            args.append("--hard-sectors")
        if "reverse" in self.config_data["gw"] and self.config_data["gw"]["reverse"] is not None:
            args.append("--reverse")

        # Add the file output as final parameter
        args.append(f"{data["data_dir"]}/{data["data_files"]["flux"]}")

        # Log all parameters to be passed to gw read
        self.log("floppy_gw_args",args,json_output=True)

        # Don't re-rip Floppy
        if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["flux"]}"):
            # Run the gw read process using arguments
            try:
                main(args)
            except Exception as e:
                print("GW FAIL - Possibly not connected?")

        # Get flux files
        fluxs = glob.glob(f"{data["data_dir"]}/*.raw")
        # If FLACs were created add them to data output
        if len(fluxs) > 0:
            data["data_files"]["flux"]=[]
            for flux in fluxs:
                data["data_files"]["flux"].append(f"{flux.replace(data["data_dir"]+"/","")}")


        data["done"]=True
        self.status(data)
        # Return all generated data
        return data



    def rip(self, media_sample):
        """Rip Floppy with greaseweazle hardware using gw software as python
        modules

        Only rips to flux, the convert step later can be used to decode flux

        """

        # Setup rip output path
        self.setProjectDir(media_sample["name"])

        # Rip and return data
        return [self.ripToFlux(media_sample)]

