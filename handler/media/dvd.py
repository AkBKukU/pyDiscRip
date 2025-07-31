#!/usr/bin/env python3

# DVD ripping module for pyDiscRip. Can be used to rip a DVD

# Python System
import os
import json
from pathlib import Path

# Internal Modules
from handler.media.media_handler import MediaHandler


class MediaHandlerDVD(MediaHandler):
    """Handler for DVD media types

    rips using a subprocess command to run `ddrescue` to create an ISO file
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="DVD"
        # Data types output
        self.data_outputs=["ISO9660"]
        # DVD info to be collected
        self.dvd_partition_filesystem=""


    def ripDVD(self, media_sample):
        """Use ddrescue to rip DVD with multiple passes and mapfile

        """
        # TODO - Data is not always ISO9660, support for UDF is needed still
        data = {
            "type_id": "ISO9660",
            "processed_by": [],
            "done": False,
            "data_dir":  self.ensureDir(f"{self.getPath()}/ISO9660/{media_sample["name"]}"),
            "data_files": {
                "ISO": [f"{media_sample["name"]}.iso"]
            }
        }
        self.status(data)

        # Don't re-rip ISO
        if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["ISO"][0]}"):

            # ddrescue is a multi step process that is run three times
            cmd1 = f"ddrescue -b 2048 -n -v \"{media_sample["drive"]}\" \"{data["data_dir"]}/{data["data_files"]["ISO"][0]}\" \"{data["data_dir"]}/mapfile\"  | tee -a ../$logs/dvd-ddrescue.log"
            cmd2 = f"ddrescue -b 2048 -d -r 3 -v \"{media_sample["drive"]}\" \"{data["data_dir"]}/{data["data_files"]["ISO"][0]}\" \"{data["data_dir"]}/mapfile\"  | tee -a ../$logs/dvd-ddrescue.log"
            cmd3 = f"ddrescue -b 2048 -d -R -r 3 -v \"{media_sample["drive"]}\" \"{data["data_dir"]}/{data["data_files"]["ISO"][0]}\" \"{data["data_dir"]}/mapfile\"  | tee -a ../$logs/dvd-ddrescue.log"

            # Run command
            self.osRun(cmd1)
            self.osRun(cmd2)
            self.osRun(cmd3)

        data["done"]=True
        self.status(data)
        # Return all generated data
        return data


    def rip(self, media_sample):
        """Rip DVD with ddrescue

        """
        print("Ripping as DVD")
        print("WARNING: This software does not yet distinguish between ISO9660 and UDF filesystems")
        # Setup rip output path
        self.setProjectDir(media_sample["name"])

        # Rip and return data
        return [self.ripDVD(media_sample)]

