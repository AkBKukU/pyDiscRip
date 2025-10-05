#!/usr/bin/env python3

# DVD ripping module for pyDiscRip. Can be used to rip a DVD

# Python System
import os
import json
from pathlib import Path

# Internal Modules
from handler.media.media_handler import MediaHandler
from handler.media.optical import MediaOptical


class MediaHandlerDVDRedumper(MediaOptical):
    """Handler for DVD media types

    rips using a subprocess command to run `ddrescue` to create an ISO file
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set handler ID
        self.handler_id="dvd_redumper"
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

        # Don't re-rip BIN/TOC
        if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["ISO"]}"):
            # Build cdrdao command to read CD
            cmd = [
                "redumper",
                "disc",
                "--retries=100",
                f"--drive={media_sample["drive"]}",
                f"--image-path={data["data_dir"]}",
                f"--image-name={media_sample["name"]}"

                ]

            # Run command
            self.osRun(cmd)

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

