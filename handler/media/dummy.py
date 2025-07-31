#!/usr/bin/env python3

# DVD ripping module for pyDiscRip. Can be used to rip a DVD

# Python System
import os
import json
from pathlib import Path
import random
import time

# Internal Modules
from handler.media.media_handler import MediaHandler


class MediaHandlerDummy(MediaHandler):
    """Handler for DVD media types

    rips using a subprocess command to run `ddrescue` to create an ISO file
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="DUMMY"
        # Data types output
        self.data_outputs=["BINARY"]
        # DVD info to be collected
        self.dvd_partition_filesystem=""


    def ripDummy(self, media_sample):
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
        count=str(int(random.random()*20))
        # ddrescue is a multi step process that is run three times
        cmd1 = f"dd bs=8M count={count} if=/dev/random of=\"{data["data_dir"]}/{data["data_files"]["BINARY"][0]}\" "

        # Run command
        result = self.osRun(cmd1)
        self.log("dd_out",str(result.stdout))
        self.log("dd_err",str(result.stderr))

        data["done"]=True
        self.status(data)
        # Return all generated data
        return data


    def rip(self, media_sample):
        """Rip DVD with ddrescue

        """
        print("Creating dummy rip of /dev/random")
        # Setup rip output path
        self.setProjectDir(self.project_dir+"/"+media_sample["name"])

        # Rip and return data
        return [self.ripDummy(media_sample)]


    def load(self,media_sample,bypass=False):
        print(f"Dummy [{media_sample["name"]}] Loading")
        time.sleep(1)


    def eject(self,media_sample):
        print(f"Dummy [{media_sample["name"]}] Done")
        time.sleep(1)
