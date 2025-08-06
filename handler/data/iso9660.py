#!/usr/bin/env python3

# ISO9660 conversion module for pyDiscRip.

# Python System
import os
import glob
import json

# Internal Modules
from handler.data.data_handler import DataHandler


class DataHandlerISO9660(DataHandler):
    """Handler for BINCUE data types

    Extracts files using 7zip
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set handle ID
        self.handle_id="DataHandlerISO9660"
        # Set data type to handle
        self.type_id="ISO9660"
        # Data types output
        self.data_outputs=["Z_FILES"]


    def convertData(self,data):
        """Use 7-zip to extract files out of ISO

        """

        # Go through all ISOs
        for iso in data["data_files"]["ISO"]:

            # Build data output files
            data_files = {
                "type_id": "Z_FILES",
                "processed_by": [],
                "data_dir": self.ensureDir(f"{data["data_dir"]}/{iso.replace(".iso","")}"),
                "data_files": {
                    "Z_FILES": f"{iso.replace(".iso","")}"
                }
            }

            print(f"Working on: {iso} => {data["data_dir"]}")

            # Build 7z command to extract files
            cmd = f"7z -y x {data["data_dir"]}/{iso} -o{data_files["data_dir"]}"

            # Run command
            result = self.osRun(cmd)
            self.log("7z_stdout",str(result.stdout.decode("utf-8")))
            self.log("7z_stderr",str(result.stderr.decode("utf-8")))

            return [data_files]

        # Only returned if an error happens
        return None
