#!/usr/bin/env python3

# Data conversion manager for pyDiscRip. Can be used to rip a CD and fetch metadata

from pprint import pprint

# Internal Modules
from handler.data.data_handler import DataHandler
from handler.data.bincue import DataHandlerBINCUE
from handler.data.bincue_split import DataHandlerBINCUESPLIT
from handler.data.iso9660 import DataHandlerISO9660
from handler.data.wav import DataHandlerWAV
from handler.data.flux import DataHandlerFLUX
from handler.data.hxc_image import DataHandlerHXCImage


class DataHandlerManager(object):
    """Manager for data types

    Provides process control functions for converting different data types and
    setting configuration data.
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Add all supported data types
        self.data_types={}
        self.data_types["BINCUE"] = DataHandlerBINCUE()
        self.data_types["BINCUE_SPLIT"] = DataHandlerBINCUESPLIT()
        self.data_types["ISO9660"] = DataHandlerISO9660()
        self.data_types["WAV"] = DataHandlerWAV()
        self.data_types["FLUX"] = DataHandlerFLUX()
        self.data_types["HXC"] = DataHandlerHXCImage()

    def configVirtual(self,config):
        """Configure a new handler to use as a virtual data format

        """
        if "Virtual" in config:
            # Add all new virtual formats
            for data in config["Virtual"]["Data"]:
                # Create and configure new handler
                self.data_types[data["input_type_id"]] = DataHandler()
                self.data_types[data["input_type_id"]].prepareVirtualFormat(data)

    def findDataType(self,data):
        """Match data handler to type and return handler

        """

        # Iterate through all handlers
        for type_id, data_handler in self.data_types.items():
            if data_handler.dataMatch(data) and not data_handler.handle_id in data["processed_by"]:
                print(f"Found handler: {data_handler.handle_id}")
                return data_handler

        return None


    def configDump(self):
        """Get all config data for media handlers and dump it to json

        """
        config_options={}
        # Iterate through all handlers
        for type_id, data_handler in self.data_types.items():
            # Add all config options for handler
            config_options[type_id]=data_handler.configOptions()

        return config_options

