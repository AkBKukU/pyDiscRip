#!/usr/bin/env python3

# WAV conversion module for pyDiscRip.

# Python System
import os, sys
import glob
import json

# External Modules
try:
    import ffmpeg
    if not "input" in dir(ffmpeg):
        print("You have the wrong ffmpeg python module installed.")
        print("Need to install Python module [ffmpeg-python]")
        sys.exit(1)

except Exception as e:
    print("Need to install Python module [ffmpeg-python]")
    sys.exit(1)

# Internal Modules
from handler.data.data_handler import DataHandler


class DataHandlerWAV(DataHandler):
    """Handler for WAV data types

    Converts files using ffmpeg
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set handle ID
        self.handle_id="DataHandlerWAV"
        # Set data type to handle
        self.type_id="WAV"
        # Data types output
        self.data_outputs=["FLAC"]


    def convertWAV(self,data,data_meta=None):
        """Use ffmpeg to convert WAVs to FLAC

        Optionally uses metadata to tag files

        TODO - I don't think this can handle CDs that did not find metadata

        """
        # Track info from metadata
        tracks = None
        # Metadata object for ffmpeg
        metadata = {}
        # Data files to process
        data_files = {}
        # Matching release for metadata
        release = {}

        # Open metadata json
        with open(f"{data_meta["data_dir"]}/{data_meta["data_files"]["JSON"]}", encoding="utf-8") as f:
            json_data = json.load(f)

            # Get discid for sample ripped
            discid = json_data["disc"]["id"]

            # Iterate through all releases in metadata
            for medium in json_data["disc"]["release-list"][0]["medium-list"]:
                for disc in medium["disc-list"]:
                    # Find matching release
                    if disc["id"] == discid:
                        release = medium
                        # break?

            # Get track data for release
            tracks = release["track-list"]

            # Build metadata for ffmpeg
            metadata = {
                "metadata:g:1": f"artist={json_data["disc"]["release-list"][0]["artist-credit-phrase"]}",
                "metadata:g:2": f"album={json_data["disc"]["release-list"][0]["title"]}",
                "metadata:g:3": f"date={int(json_data["disc"]["release-list"][0]["date"][0:4])}"
            }

            # Build data output for FLAC
            data_files = {
                "type_id": "FLAC",
                "processed_by": [],
                "data_dir": self.ensureDir(f"{self.getPath()}/FLAC/{self.cleanFilename(json_data["disc"]["release-list"][0]["artist-credit-phrase"])}/{json_data["disc"]["release-list"][0]["date"][0:4]} - {self.cleanFilename(json_data["disc"]["release-list"][0]["title"])}"),
                "data_files": {
                    "FLAC": []
                }
            }

        # Iterate over WAV files
        for i,v in enumerate(data["data_files"]["WAV"]):
            print(f"Working on: {data["data_files"]["WAV"][i]}: {self.cleanFilename(tracks[i]["recording"]["title"])}")
            # Set track title in ffmpeg metadata
            metadata["metadata:g:0"] = f"title={tracks[i]["recording"]["title"]}"

            # Run ffmpeg to conver WAV to FLAC
            (ffmpeg
                .input(f"{data["data_dir"]}/{data["data_files"]["WAV"][i]}")
                .output(f"{data_files["data_dir"]}/{(i+1):02} - {self.cleanFilename(tracks[i]["recording"]["title"])}.flac", **metadata)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

        # Get FLAC files
        flacs = glob.glob(f"{data_files["data_dir"]}/*.flac")
        # If FLACs were created add them to data output
        if len(flacs) > 0:
            for flac in flacs:
                data_files["data_files"]["FLAC"].append(f"{flac.replace(data_files["data_dir"]+"/","")}")
        return data_files


    def convert(self, media_sample):
        """Take in WAV and convert to FLACs with taging if available

        """

        # Setup rip output path
        self.setProjectDir(media_sample["name"])

        # Go through all data in media sample
        for data in media_sample["data"]:
            # Check handler can work on data
            if data["type_id"] == self.type_id:
                # Check if handler has already worked on data
                if self.type_id not in data["processed_by"]:
                    print("Convert WAV to FLAC")

                    # Check for metadata
                    data_meta=None
                    for data_sup in media_sample["data"]:
                        if data_sup["type_id"] == "MUSICBRAINZ":
                            data_meta=data_sup

                    # Convert data
                    data_output = self.convertWAV(data, data_meta)

                    if data_output is not None:
                        # Mark data as processed
                        data["processed_by"].append(self.type_id)
                        media_sample["data"].append(data_output)

        # Return media sample with new data
        return media_sample
