#!/usr/bin/env python3

# BINCUE conversion module for pyDiscRip.

# Python System
import os
import glob
import sys
import json

# Internal Modules
from handler.data.data_handler import DataHandler


class DataHandlerBINCUE(DataHandler):
    """Handler for BINCUE data types

    Extracts files using bchunk
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set data type to handle
        self.type_id="BINCUE"
        # Data types output
        self.data_outputs=["WAV","ISO9660"]


    def convertData(self,data_in):
        """Use bchunk to extract all WAVs and ISOs from BINCUE

        """
        # Build data output for WAV
        data_wav = {
            "type_id": "WAV",
            "processed_by": [],
            "data_dir": self.ensureDir(f"{self.getPath()}/WAV/{data_in["data_files"]["BIN"].replace(".bin","")}"),
            "data_files": {
                "WAV": []
            }
        }

        # Build data output ISO
        data_iso = {
            "type_id": "ISO9660",
            "processed_by": [],
            "data_dir": self.ensureDir(f"{self.getPath()}/ISO9660/{data_in["data_files"]["BIN"].replace(".bin","")}"),
            "data_files": {
                "ISO": []
            }
        }

        # Check for files in ouput directory
        wavs = glob.glob(f"{data_wav["data_dir"]}/*.wav")
        isos = glob.glob(f"{data_iso["data_dir"]}/*.iso")

        # Don't re-convert if files exist
        if len(wavs) == 0 and len(isos) == 0 :
            # Build bchunk command to generate CUE
            cmd = f"bchunk -w {data_in["data_dir"]}/{data_in["data_files"]["BIN"]} {data_in["data_dir"]}/{data_in["data_files"]["CUE"]} {data_wav["data_dir"]}/track"

            # Run command
            self.osRun(cmd)


        # Get files in ouput directory
        wavs = glob.glob(f"{data_wav["data_dir"]}/*.wav")
        # Sort wavs to have file order make sense
        wavs.sort()

        #  Build data output if WAVs were converted
        if len(wavs) > 0:

            # Add file paths to data output for all WAVs
            for wav in wavs:
                print(f"Working on: {wav}")
                data_wav["data_files"]["WAV"].append(f"{wav.replace(data_wav["data_dir"]+"/","")}")

        #  Build data output if ISOs were converted
        isos = glob.glob(f"{data_wav["data_dir"]}/*.iso") + glob.glob(f"{data_iso["data_dir"]}/*.iso")
        if len(isos) > 0:

            # Add file paths to data output for all ISOs
            for iso in isos:
                print(f"Working on: {iso}")
                # The file paths get weird, this is a fix for it
                if "WAV" in iso:
                    os.rename(
                        iso,
                        f"{data_iso["data_dir"]}/{iso.replace(data_wav["data_dir"]+"/","")}")
                    iso = f"{data_iso["data_dir"]}/{iso.replace(data_wav["data_dir"]+"/","")}"
                data_iso["data_files"]["ISO"].append(f"{iso.replace(data_iso["data_dir"]+"/","")}")

        # Clear WAV data if no WAVs were created
        if len(wavs) == 0:
            data_wav = None

        # Clear ISO data if no ISOs were created
        if len(isos) == 0:
            data_iso = None

        # Return all generated data
        return [data_wav,data_iso]

