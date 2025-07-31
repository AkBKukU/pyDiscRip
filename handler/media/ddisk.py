#!/usr/bin/env python3

# DVD ripping module for pyDiscRip. Can be used to rip a DVD

# Python System
import os
import json
from pathlib import Path

# Internal Modules
from handler.media.media_handler import MediaHandler


class MediaHandlerDDisk(MediaHandler):
    """Handler for DVD media types

    rips using a subprocess command to run `ddrescue` to create an ISO file
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="DDISK"
        # Data types output
        self.data_outputs=["BINARY"]
        # DVD info to be collected
        self.dvd_partition_filesystem=""


    def ripDD(self, media_sample):
        """Use ddrescue to rip DVD with multiple passes and mapfile

        """
        data = {
            "type_id": "BINARY",
            "processed_by": [],
            "done": False,
            "data_dir":  self.ensureDir(f"{self.project_dir}/BINARY/{media_sample["name"]}"),
            "data_files": {
                "BINARY": [f"{media_sample["name"]}.img"]
            }
        }
        self.status(data)

        # Don't re-rip ISO
        # if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["BINARY"][0]}"):

        # ddrescue is a multi step process that is run three times
        cmd1 = f"ddrescue -b 2048 -n -v \"{media_sample["drive"]}\" \"{data["data_dir"]}/{data["data_files"]["BINARY"][0]}\" \"{data["data_dir"]}/mapfile\"  | tee -a ../$logs/dvd-ddrescue.log"
        cmd2 = f"ddrescue -b 2048 -d -r 3 -v \"{media_sample["drive"]}\" \"{data["data_dir"]}/{data["data_files"]["BINARY"][0]}\" \"{data["data_dir"]}/mapfile\"  | tee -a ../$logs/dvd-ddrescue.log"
        cmd3 = f"ddrescue -b 2048 -d -R -r 3 -v \"{media_sample["drive"]}\" \"{data["data_dir"]}/{data["data_files"]["BINARY"][0]}\" \"{data["data_dir"]}/mapfile\"  | tee -a ../$logs/dvd-ddrescue.log"

        # Run command
        result = self.osRun(cmd1)
        self.log("ddrescue_1-3_out",str(result.stdout))
        self.log("ddrescue_1-3_err",str(result.stderr))
        result = self.osRun(cmd2)
        self.log("ddrescue_2-3_out",str(result.stdout))
        self.log("ddrescue_2-3_err",str(result.stderr))
        result = self.osRun(cmd3)
        self.log("ddrescue_3-3_out",str(result.stdout))
        self.log("ddrescue_3-3_err",str(result.stderr))

        data["done"]=True
        self.status(data)
        # Return all generated data
        return data


    def rip(self, media_sample):
        """Rip DVD with ddrescue

        """
        print("Ripping as generic disk with ddrescue")
        # Setup rip output path
        self.setProjectDir(self.project_dir+"/"+media_sample["name"])

        # Rip and return data
        return [self.ripDD(media_sample)]

