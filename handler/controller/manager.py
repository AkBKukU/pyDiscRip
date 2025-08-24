#!/usr/bin/env python3

# Media ripping manager for pyDiscRip. Can be used to rip a CD and fetch metadata

# External Modules
import pyudev
from pprint import pprint

# Internal Modules
from handler.controller.RoboRacerLS import ControllerRoboRacerLS
from handler.controller.AutoPublisherLS import ControllerAutoPublisherLS
from handler.controller.gw import ControllerGw
# Testing only
from handler.media.dummy import MediaHandlerDummy

class ControllerHandlerManager(object):
    """Manager for controllers
.
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()

        # Add all supported media types
        self.controller_types={}
        self.controller_types["RoboRacerLS"] = ControllerRoboRacerLS()
        self.controller_types["AutoPublisherLS"] = ControllerAutoPublisherLS()
        self.controller_types["Greaseweazle"] = ControllerGw()

    def getController(self,controller_type):
        return(self.controller_types[controller_type])

