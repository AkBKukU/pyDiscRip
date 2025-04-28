#!/usr/bin/env python3

# Base data handler for pyDiscRip.

# Python System
import sys, os
import json
from enum import Enum
from datetime import datetime

# Internal Modules
from handler.handler import Handler


class Data(Enum):
    """Data types currently supported

    """
    BINCUE="BINCUE"
    MUSICBRAINZ="MUSICBRAINZ"
    WAV="WAV"
    FLAC="FLAC"
    ISO9660="ISO9660"
    FLUX="FLUX"
    FAT12="FAT12"
    BINARY="BINARY" # Will want a subtype associated in the data_sample
    Z_FILES="Z_FILES" # Special type for indeterminate files


class DataHandler(Handler):
    """Base class for Data Types to handle identification and conversion

    Data dict structure example:
{
    data_id: Data.BINCUE,
    data_dir: "some-folder",
    data_processed: False,
    data_files: {
        "BIN": name.bin,
        "cue": name.cue,
        "toc": name.toc
    }
}

    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set data type id for later use
        self.data_id=None
        # Set directory to work in
        self.project_dir="./"
        # Get current datetime
        self.project_timestamp=str(datetime.now().isoformat()).replace(":","-")
        # Data types output for later use
        self.data_outputs=[]


    def dataMatch(self, data_sample=None):
        """Check if the data sample should be handled by this type"""
        return data_sample["data_id"] == self.data_id

