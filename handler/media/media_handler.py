#!/usr/bin/env python3

# Base media handler for pyDiscRip.

# Python System
import sys, os
import json
from enum import Enum
from datetime import datetime

# Internal Modules
from handler.handler import Handler


class MediaHandler(Handler):
    """Base class for Media Types to handle identification and ripping

    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type id for later use
        self.type_id=None
        # Set directory to work in
        self.project_dir=""
        # Get current datetime
        self.project_timestamp=str(datetime.now().isoformat()).replace(":","-")
        # Data types output for later use
        self.data_outputs=[]


    def mediaMatch(self, media_sample=None):
        """Check if the media sample should be handled by this type"""
        return media_sample["media_type"] == self.type_id

