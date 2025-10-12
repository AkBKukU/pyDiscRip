#!/usr/bin/env python3

# Media ripping manager for pyDiscRip. Can be used to rip a CD and fetch metadata

# External Modules
import time, sys
import json
from pprint import pprint
import pathlib
try:
    import pyudev
except Exception as e:
        print("Need to install Python module [pyudev]")
        sys.exit(1)

# Internal Modules
from handler.media.optical import MediaOptical
from handler.media.cd import MediaHandlerCD
from handler.media.cd_redumper import MediaHandlerCDRedumper
from handler.media.dvd import MediaHandlerDVD
from handler.media.dvd_redumper import MediaHandlerDVDRedumper
from handler.media.bd_redumper import MediaHandlerBDRedumper
from handler.media.ddisk import MediaHandlerDDisk
from handler.media.floppy import MediaHandlerFloppy
# Testing only
from handler.media.dummy import MediaHandlerDummy

class MediaHandlerManager(object):
    """Manager for media types

    Provides process control functions for ripping different media types and
    setting configuration data.
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()

        # Add all supported media types
        self.media_types={}
        self.media_types["OPTICAL"] = MediaOptical()
        self.media_types["CD_cdrdao"] = MediaHandlerCD()
        self.media_types["CD_redumper"] = MediaHandlerCDRedumper()
        self.media_types["DVD"] = MediaHandlerDVD()
        self.media_types["DVD_redumper"] = MediaHandlerDVDRedumper()
        self.media_types["BD_redumper"] = MediaHandlerBDRedumper()
        self.media_types["DDISK"] = MediaHandlerDDisk()
        self.media_types["FLOPPY"] = MediaHandlerFloppy()
        # Testing only
        self.media_types["DUMMY"] = MediaHandlerDummy()

    def loadMediaType(self,media_sample,bypass=False,controller=None):
        """Match media handler to type and return handler

        """
        # Iterate through all handlers
        for type_id, media_type in self.media_types.items():
            # If handler can proccess media return it
            if media_type.mediaMatch(media_sample):
                # Set controller
                media_type.controller = controller
                return media_type.load(media_sample,bypass)

        # No handlers found

    def ejectMediaType(self,media_sample,controller=None):
        """Match media handler to type and return handler

        """
        print("Ejecting through manager")
        # Iterate through all handlers
        for type_id, media_type in self.media_types.items():
            # If handler can proccess media return it
            if media_type.mediaMatch(media_sample):
                print(f"Matched: {type_id}")
                # Set controller
                media_type.controller = controller
                media_type.eject(media_sample)
                return

        # Generic optical
        print("No match found, attempting generic optical")
        if typeIsOptical(selfmedia_sample):
            self.media_types["OPTICAL"].eject(media_sample)
        # No handlers found
        return


    def findMediaType(self,media_sample,config_data):
        """Match media handler to type and return handler

        """
        # Check if a media type was provided
        if "media_type" not in media_sample or media_sample["media_type"].upper() == "OPTICAL":
            # Access the drive associated to the media to determine the type
            print("Finding media type")
            media_sample["media_type"] = self.guessMediaType(media_sample["drive"])

        # Iterate through all handlers
        for type_id, media_type in self.media_types.items():
            # If handler can proccess media return it
            if media_type.mediaMatch(media_sample):
                if media_type.handler_id == None:
                    return media_type
                if config_data["settings"]["media_handlers"][media_sample["media_type"]] == media_type.handler_id:
                    return media_type

        # No handlers found
        print(f"No handlers found for following media sample:")
        pprint(media_sample)
        return None


    def configDump(self):
        """Get all config data for media handlers and dump it to json

        """
        config_options={}
        # Iterate through all handlers
        for type_id, media_type in self.media_types.items():
            # Add all config options for handler
            config_options[type_id]=media_type.configOptions()

        return config_options


    def guessMediaType(self,drivepath=None):
        """ Guess media type in drive which will determine how it is ripped

        Only useful for optical discs.
        """

        # Init udev interface to access drive
        context = pyudev.Context()

        # Countdown to assume it's a weird CD
        countdown = 10

        # Get info from device
        output = True
        while(output):
            print("FIND A DISC TYPE")
            #print(f"Drive path: {drivepath}")

            # Solve and symlinks to standard drive path
            drivepath=str(pathlib.Path(drivepath).resolve())
            # NOTE: Returns as list but we are accessing a specific device
            devices = context.list_devices(sys_name=drivepath.replace("/dev/",""))
            dev = next(iter(devices))

            #print(json.dumps(dict(dev.properties),indent=4))
            # Determine media type by ID
            if dev.properties.get("ID_CDROM_MEDIA_CD", False) or dev.properties.get("ID_CDROM_MEDIA_CD_R", False):
                media_type="CD"
                output = False
                print("Is CD")
            elif dev.properties.get("ID_CDROM_MEDIA_DVD", False):
                media_type="DVD"
                output = False
                print("Is DVD")
            elif dev.properties.get("ID_CDROM_MEDIA_BD", False):
                media_type="BD"
                output = False

            if output:
                countdown-=1
                if not countdown:
                    media_type="CD"
                    output = False
                    print("Is probably a weird CD")

            #print(json.dumps(dict(dev.properties),indent=4))
            time.sleep(3)

        return media_type

    def typeIsOptical(selfmedia_sample):

        # Generic optical
        match media_sample.type_id:
            case "CD" | "DVD"| "BD" | "CD_cdrdao" | "CD_redumper":
                return True
            case _:
                return False


