#!/usr/bin/env python3

# Floppy ripping module for pyDiscRip. Uses greaseweazle hardware

# Python System
import os
import json
import glob
from pathlib import Path
import importlib
from pprint import pprint
import time

# External Modules
# Directly imports from greaseweazle module in code

# Internal Modules
from handler.media.media_handler import MediaHandler

# from handler.controller.gw import ControllerGw

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

        try:
            # Import greaseweazle read module to access hardware
            mod = importlib.import_module('greaseweazle.tools.read')
        except Exception as e:
            print("Need to install greaseweazle software:")
            print("pip install git+https://github.com/keirf/greaseweazle@latest --force")
            sys.exit(1)

        main = mod.__dict__['main']

        # gw modules individually parse arguments to control rip process. This
        # builds fake argumets to pass to module
        # For more information on gw parameters run `gw read --help`
        args=[]
        args.append("pyDiscRip") # Not actually used but index position is needed
        args.append("read") # Not actually used but index position is needed
        args.append("--drive")
        args.append(media_sample["drive"].split("@")[0])

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
        if "@" in media_sample["drive"]:
            args.append("--device")
            args.append(media_sample["drive"].split("@")[1])
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
        # Lock drive bus
        if self.controller is not None:
            self.controller.floppy_bus_check(True)

        # Setup rip output path
        self.setProjectDir(media_sample["name"])

        # Rip and return data
        data = self.ripToFlux(media_sample)

        # Unlock drive bus
        if self.controller is not None:
            self.controller.floppy_bus_check(False)

        # Rip and return data
        return [data]


    def eject(self,media_sample):
        """Eject drive tray
        """
        time.sleep(1)

    def load(self,media_sample,bypass=False):
        """Load media before continuing.

        Default method call waits for user to press enter

        Overload with automatic methods where possible.
        """
        config_data=media_sample["config_data"]
        print(f"Please load [{media_sample["name"]}] into [{media_sample["drive"]}]")
        if self.controller is not None:
            self.web_update({"drive_status":{media_sample["drive"]:{"status":3,"title":f"Please load [{media_sample["name"]}] into [{media_sample["drive"]}]"}}},media_sample["config_data"])
            self.controller.load_hold(callback=MediaHandler.web_after_action,callback_arg={"url":f"http://{config_data["settings"]["web"]["ip"]}:{config_data["settings"]["web"]["port"]}/status/drive_status.json","drive":media_sample["drive"]})

            self.web_update({"drive_status":{media_sample["drive"]:{"status":2,"title":f"Waiting for bus to be free"}}},media_sample["config_data"])
            self.controller.floppy_bus_check()
            return

        if bypass:
            # Allow skipping blocking to handle externally
            return
        input(f"Please load [{media_sample["name"]}] into [{media_sample["drive"]}]")
