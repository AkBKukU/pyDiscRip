#!/usr/bin/env python3

# split BINCUE merging module for pyDiscRip.

# Python System
import os
import glob
import sys
import json

# Internal Modules
from handler.data.data_handler import DataHandler
from handler.util.bincon import cue_by_line


class DataHandlerBINCUESPLIT(DataHandler):
    """Handler for split BINCUE data types

    Merges files using bincon
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set handle ID
        self.handle_id="DataHandlerBINCUESPLIT"
        # Set data type to handle
        self.type_id="BINCUE_SPLIT"
        # Data types output
        self.data_outputs=["BINCUE"]


    def convertData(self,data_in):
        """Use bchunk to extract all WAVs and ISOs from BINCUE

        """
        # Build data output
        data = {
            "type_id": "BINCUE",
            "processed_by": [],
            "done": False,
            "data_dir": self.ensureDir(f"{self.getPath()}/BINCUE/"),
            "data_files": {
                "BIN": f"{data_in["data_files"]["CUE"].replace(".cue","")}.bin",
                "CUE": f"{data_in["data_files"]["CUE"].replace(".cue","")}.cue"
            }
        }

        # Merge BIN files
        cue_by_line(data_in["data_dir"]+"/"+data_in["data_files"]["CUE"], data_in["data_files"]["CUE"].replace(".cue",""),path=data["data_dir"])


        # Get files in output directory
        bins = list(map(os.path.basename, glob.glob(f"{data["data_dir"]}/*.bin")))
        # Sort wavs to have file order make sense
        bins.sort()
        data["data_files"]["BIN"] = bins


        # Return all generated data
        return [data]

